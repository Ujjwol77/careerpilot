"use client";
import { useState } from "react";
import { api, ApiError, useApi } from "@/lib/api";
import { Card, ErrorBox, Loading, NeedCv, PageHeader, Pill, ScoreRing, bandLabel, bandTone, money } from "@/components/ui";

/* eslint-disable @typescript-eslint/no-explicit-any */
export default function JobsPage() {
  const [tab, setTab] = useState<"matches" | "search">("matches");
  return (
    <>
      <PageHeader title="Jobs and matching" subtitle="The Job Search and Job Matching agents work together to rank postings for you." />
      <div className="tabs" role="group" aria-label="View">
        <button aria-pressed={tab === "matches"} onClick={() => setTab("matches")}>Best matches</button>
        <button aria-pressed={tab === "search"} onClick={() => setTab("search")}>Browse all</button>
      </div>
      {tab === "matches" ? <Matches /> : <Search />}
    </>
  );
}

function Track({ jobId }: { jobId: number }) {
  const [state, setState] = useState<"idle" | "busy" | "done" | "err">("idle");
  const [msg, setMsg] = useState("");
  async function go() {
    setState("busy");
    try { await api("/applications", { body: { job_id: jobId } }); setState("done"); }
    catch (e) {
      if (e instanceof ApiError && e.code === "ALREADY_TRACKED") setState("done");
      else { setState("err"); setMsg(e instanceof Error ? e.message : "Failed"); }
    }
  }
  return (
    <>
      <button className="btn btn-ghost btn-small" onClick={go} disabled={state === "busy" || state === "done"}>
        {state === "done" ? "Tracked ✓" : "Track"}
      </button>
      {state === "err" && <span className="small" role="alert" style={{ color: "var(--bad)" }}> {msg}</span>}
    </>
  );
}

function Matches() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  async function run() {
    setBusy(true); setError(null);
    try { setData(await api("/jobs/match", { method: "POST" })); }
    catch (e) { setError(e instanceof ApiError ? e : null); }
    finally { setBusy(false); }
  }

  return (
    <>
      <div className="row no-print" style={{ marginBottom: 14 }}>
        <button className="btn" onClick={run} disabled={busy}>{busy ? "Matching…" : data ? "Re-run matching" : "Find my matches"}</button>
        <span className="muted small">Uses your profile and preferences.</span>
      </div>
      <NeedCv error={error} />
      {data && (
        <>
          <Card title="Agent workflow">
            <div className="row">
              {data.agent_trace.map((s: any, i: number) => (
                <Pill key={i} tone={s.status === "ok" ? "good" : "bad"}>{s.agent.replaceAll("_", " ")}: {s.note}</Pill>
              ))}
            </div>
          </Card>
          <Card title={`${data.count} matches`}>
            {data.count === 0 && <p className="muted">No postings matched. Loosen your preferences and try again.</p>}
            {data.matches.map((m: any) => (
              <div className="job" key={m.job_id}>
                <ScoreRing value={m.score} label={`Match score for ${m.title}`} />
                <div className="job-body">
                  <div className="spread">
                    <div><strong>{m.title}</strong><div className="muted small">{m.company} · {m.location} · {money(m.salary_min)}–{money(m.salary_max)}</div></div>
                    <Track jobId={m.job_id} />
                  </div>
                  <Pill tone={bandTone(m.readiness)}>{bandLabel(m.readiness)}</Pill>
                  <div className="small">
                    {m.matched_skills.length > 0 && <p><strong>You have:</strong> {m.matched_skills.join(", ")}</p>}
                    {m.missing_skills.length > 0 && <p><strong>Missing:</strong> {m.missing_skills.join(", ")}</p>}
                  </div>
                  <details>
                    <summary>Why this score?</summary>
                    <table>
                      <tbody>
                        <tr><td>Semantic similarity (35%)</td><td>{Math.round(m.components.semantic * 100)}%</td></tr>
                        <tr><td>Skill coverage (50%)</td><td>{Math.round(m.components.skill_coverage * 100)}%</td></tr>
                        <tr><td>Experience fit (15%)</td><td>{Math.round(m.components.experience_fit * 100)}%</td></tr>
                      </tbody>
                    </table>
                  </details>
                </div>
              </div>
            ))}
          </Card>
        </>
      )}
    </>
  );
}

function Search() {
  const meta = useApi<{ roles: { key: string; label: string }[] }>("/meta");
  const [f, setF] = useState({ q: "", role: "", location: "", min_salary: "", level: "" });
  const [applied, setApplied] = useState(f);
  const { data, error, loading } = useApi<{ count: number; jobs: any[] }>("/jobs/search", applied);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value });

  return (
    <>
      <Card>
        <form onSubmit={(e) => { e.preventDefault(); setApplied(f); }}>
          <div className="grid grid-3">
            <div className="field"><label htmlFor="q">Keywords</label><input id="q" value={f.q} onChange={set("q")} placeholder="SQL, security, React…" /></div>
            <div className="field"><label htmlFor="role">Role</label>
              <select id="role" value={f.role} onChange={set("role")}><option value="">Any</option>{meta.data?.roles.map((r) => <option key={r.key} value={r.key}>{r.label}</option>)}</select></div>
            <div className="field"><label htmlFor="loc">Location</label><input id="loc" value={f.location} onChange={set("location")} placeholder="Perth" /></div>
            <div className="field"><label htmlFor="min">Min salary</label><input id="min" type="number" min={0} step={5000} value={f.min_salary} onChange={set("min_salary")} /></div>
            <div className="field"><label htmlFor="lvl">Level</label>
              <select id="lvl" value={f.level} onChange={set("level")}><option value="">Any</option><option>junior</option><option>mid</option><option>senior</option></select></div>
          </div>
          <button className="btn">Search</button>
        </form>
      </Card>
      <ErrorBox error={error} />
      {loading ? <Loading /> : (
        <Card title={`${data?.count ?? 0} postings`}>
          <p className="muted small">Postings come from a synthetic seed dataset with fictional companies. Real job APIs plug in through the JobSource interface.</p>
          {data?.jobs.map((j) => (
            <div className="job" key={j.id}>
              <div className="job-body">
                <div className="spread">
                  <div><strong>{j.title}</strong><div className="muted small">{j.company} · {j.location} · {j.level} · {money(j.salary_min)}–{money(j.salary_max)}</div></div>
                  <Track jobId={j.id} />
                </div>
                <p className="small">{j.description}</p>
              </div>
            </div>
          ))}
        </Card>
      )}
    </>
  );
}
