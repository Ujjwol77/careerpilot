"use client";
import { useEffect, useState } from "react";
import { api, ApiError, saved, useApi, type Meta } from "@/lib/api";
import { Card, ErrorBox, Loading, NeedCv, PageHeader, Pill, ScoreRing, bandLabel, bandTone, money } from "@/components/ui";
import { Donut, Kpi, Legend, StackBar } from "@/components/charts";

/* eslint-disable @typescript-eslint/no-explicit-any */
export default function JobsPage() {
  const [tab, setTabState] = useState<"matches" | "search">("matches");
  useEffect(() => { if (saved.get("jobs.tab") === "search") setTabState("search"); }, []);
  const setTab = (t: "matches" | "search") => { setTabState(t); saved.set("jobs.tab", t); };
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

/** What each agent step in the workflow card does, shown on hover. */
const STEP_TIPS: Record<string, string> = {
  job_search: "Job Search agent: collects postings for your target roles from Adzuna (live ads) and the sample set, then applies your location, salary and level filters. A cached search reuses ads fetched in the last 12 hours. If fewer than 3 pass the filters, it relaxes them and searches again.",
  job_matching: "Job Matching agent: scores every posting out of 100 from skills you have (50%), how closely your CV's meaning matches the advert (35%, using an AI embedding model) and your experience (15%). If the best score is under 35, it widens the search to every role.",
};

function Matches() {
  const [data, setData] = useState<any>(null);
  const [ranAt, setRanAt] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  // show the last results again after switching tabs or pages (kept until sign-out or a new CV/preferences)
  useEffect(() => {
    const last = saved.get<{ data: any; at: string }>("jobs.match");
    if (last) { setData(last.data); setRanAt(last.at); }
  }, []);

  async function run() {
    setBusy(true); setError(null);
    try {
      const result = await api("/jobs/match", { method: "POST" });
      const at = new Date().toISOString();
      setData(result); setRanAt(at);
      saved.set("jobs.match", { data: result, at });
    }
    catch (e) { setError(e instanceof ApiError ? e : null); }
    finally { setBusy(false); }
  }

  return (
    <>
      <div className="row no-print" style={{ marginBottom: 14 }}>
        <button className="btn" onClick={run} disabled={busy}>{busy ? "Matching…" : data ? "Re-run matching" : "Find my matches"}</button>
        <span className="muted small">
          {data && ranAt
            ? `Results from ${new Date(ranAt).toLocaleString(undefined, { weekday: "short", hour: "numeric", minute: "2-digit" })}. Re-run after changing your CV or preferences, or to fetch new postings.`
            : "Uses your profile and preferences."}
        </span>
      </div>
      <NeedCv error={error} />
      {data && (
        <>
          <Card title="Agent workflow" info={<>The agents that produced these results, in the order they ran, with what each one did. Green means the step worked.
            <span style={{ display: "block", marginTop: 6 }}>&quot;Reflected&quot; means the agent checked its own result, found it too weak and tried again with wider settings. Hover each step for details.</span></>}>
            <div className="row">
              {data.agent_trace.map((s: any, i: number) => (
                <Pill key={i} tone={s.status === "ok" ? "good" : "bad"} tip={STEP_TIPS[s.agent]}>{s.agent.replaceAll("_", " ")}: {s.note}</Pill>
              ))}
            </div>
          </Card>
          {data.count > 0 && (
            <div className="grid grid-2">
              <Card title="Matches by readiness" info={`Your top ${data.count} matches, grouped by match score. Hover a band for what it means.`}>
                <Donut ariaLabel="Matches grouped by readiness band" centerLabel="matches" slices={[
                  { label: "Highly qualified", color: "var(--good)", value: data.matches.filter((m: any) => m.readiness === "HIGHLY_QUALIFIED").length,
                    note: "Match score 80 or more: your CV already shows most of what these adverts ask for. Apply now." },
                  { label: "Qualified with gaps", color: "var(--warn)", value: data.matches.filter((m: any) => m.readiness === "QUALIFIED_WITH_GAPS").length,
                    note: "Match score 60 to 79: a good fit with a few missing skills. Worth applying while you close the gaps." },
                  { label: "Development required", color: "var(--bad)", value: data.matches.filter((m: any) => m.readiness === "DEVELOPMENT_REQUIRED").length,
                    note: "Match score under 60: several core skills or the experience asked for are missing. See Skill gaps." },
                ].filter((s) => s.value > 0)} />
              </Card>
              <div className="stack">
                <Kpi label="Best match score" value={Math.max(...data.matches.map((m: any) => m.score))} decimals={0} suffix="/100" accent="var(--s1)"
                  tip="The highest match score among your matches, out of 100: 50% skills you have, 35% how closely your CV's meaning matches the advert, 15% experience. It is the first job in the list below." />
                <Kpi label="Average score" value={data.matches.reduce((a: number, m: any) => a + m.score, 0) / data.count} decimals={0} suffix="/100" accent="var(--s2)"
                  tip={`The average match score of your top ${data.count} matches. It rises when you add skills that many of these adverts ask for; a big gap from the best score means only a few jobs fit you closely.`} />
              </div>
            </div>
          )}
          <Card title={`${data.count} matches`} info="Each ring is the job's match score out of 100. The bar under each job splits it into meaning (up to 35), skills (up to 50) and experience (up to 15); hover a part for your own numbers.">
            <Legend items={[{ label: "Meaning (35%)", color: "var(--s1)" }, { label: "Skills (50%)", color: "var(--s2)" }, { label: "Experience (15%)", color: "var(--s3)" }]} />
            {data.count === 0 && <p className="muted">No postings matched. Loosen your preferences and try again.</p>}
            {data.count > 0 && <SourceNote items={data.matches} />}
            {data.matches.map((m: any) => (
              <div className="job" key={m.job_id}>
                <ScoreRing value={m.score} label={`Match score for ${m.title}`} size={72} />
                <div className="job-body">
                  <div className="spread">
                    <div><strong>{m.title}</strong> <SourceBadge source={m.source} /><div className="muted small">{m.company} · {m.location} · {salaryText(m.salary_min, m.salary_max)}</div><PostingLink url={m.url} source={m.source} /></div>
                    <Track jobId={m.job_id} />
                  </div>
                  <Pill tone={bandTone(m.readiness)}>{bandLabel(m.readiness)}</Pill>
                  <div className="small">
                    {m.matched_skills.length > 0 && <p><strong>You have:</strong> {m.matched_skills.join(", ")}</p>}
                    {m.missing_skills.length > 0 && <p><strong>Missing:</strong> {m.missing_skills.join(", ")}</p>}
                  </div>
                  <StackBar ariaLabel={`How the score for ${m.title} is made up`} parts={[
                    { label: "Meaning match", value: m.components.semantic * 35, color: "var(--s1)", note: `${Math.round(m.components.semantic * 100)}% similar in meaning to your CV (${engineLabel(m.semantic_engine)}), worth up to 35` },
                    { label: "Skill coverage", value: m.components.skill_coverage * 50, color: "var(--s2)", note: `${Math.round(m.components.skill_coverage * 100)}% of required skills, worth up to 50` },
                    { label: "Experience fit", value: m.components.experience_fit * 15, color: "var(--s3)", note: `${Math.round(m.components.experience_fit * 100)}% fit, worth up to 15` },
                  ]} />
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
  const meta = useApi<Meta>("/meta");
  const blank = { q: "", field: "", role: "", location: "", min_salary: "", level: "" };
  const [f, setF] = useState(blank);
  const [applied, setAppliedState] = useState<typeof blank | null>(null); // null until the saved filters are restored
  useEffect(() => {
    const last = saved.get<typeof blank>("jobs.search");
    if (last) setF({ ...blank, ...last });
    setAppliedState(last ? { ...blank, ...last } : blank);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const setApplied = (v: typeof blank) => { setAppliedState(v); saved.set("jobs.search", v); };
  const { data, error, loading } = useApi<{ count: number; jobs: any[] }>(applied ? "/jobs/search" : null, applied ?? undefined);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value });

  return (
    <>
      <Card>
        <form onSubmit={(e) => { e.preventDefault(); setApplied(f); }}>
          <div className="grid grid-3">
            <div className="field"><label htmlFor="q">Keywords</label><input id="q" value={f.q} onChange={set("q")} placeholder="SQL, security, React…" /></div>
            <div className="field"><label htmlFor="field">Field</label>
              <select id="field" value={f.field} onChange={(e) => {
                const field = e.target.value; // keep the role only if it belongs to the new field
                const keep = !field || meta.data?.roles.some((r) => r.key === f.role && r.field === field);
                setF({ ...f, field, role: keep ? f.role : "" });
              }}>
                <option value="">Any</option>{meta.data?.fields.map((x) => <option key={x.key} value={x.key}>{x.label}</option>)}
              </select></div>
            <div className="field"><label htmlFor="role">Role</label>
              <select id="role" value={f.role} onChange={(e) => {
                const role = e.target.value;
                setF({ ...f, role, field: meta.data?.roles.find((r) => r.key === role)?.field ?? f.field });
              }}>
                <option value="">{f.field ? "Any role in this field" : "Any"}</option>
                {meta.data?.fields.filter((x) => !f.field || x.key === f.field).map((x) => (
                  <optgroup key={x.key} label={x.label}>{x.roles.map((r) => <option key={r.key} value={r.key}>{r.label}</option>)}</optgroup>
                ))}
              </select></div>
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
          <SourceNote items={data?.jobs ?? []} />
          {data?.jobs.map((j) => (
            <div className="job" key={j.id}>
              <div className="job-body">
                <div className="spread">
                  <div><strong>{j.title}</strong> <SourceBadge source={j.source} /><div className="muted small">{j.company} · {j.location} · {j.level} · {salaryText(j.salary_min, j.salary_max)}</div><PostingLink url={j.url} source={j.source} /></div>
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

function salaryText(min: number, max: number) {
  if (!min && !max) return "Salary not listed";
  if (!max || min === max) return money(min || max);
  return `${money(min)}–${money(max)}`;
}

function PostingLink({ url, source }: { url?: string; source?: string }) {
  if (!url) return null;
  return (
    <a className="small" href={url} target="_blank" rel="noopener noreferrer">
      View and apply{source === "adzuna" ? " on Adzuna" : ""}
    </a>
  );
}

/** Adzuna's terms ask apps to credit them wherever their listings are shown. */
function SourceNote({ items }: { items: { source?: string }[] }) {
  const live = items.some((i) => i.source === "adzuna");
  return live ? (
    <p className="muted small">
      Live postings: <a href="https://www.adzuna.com.au" target="_blank" rel="noopener noreferrer">Jobs by Adzuna</a>
    </p>
  ) : (
    <p className="muted small">Showing sample postings (fictional companies). Add an Adzuna key in backend/.env for live Australian jobs.</p>
  );
}

/** Shows at a glance whether a posting is a live Adzuna advert or one of the sample jobs. */
function SourceBadge({ source }: { source?: string }) {
  return source === "adzuna" ? <Pill tone="good">Live · Adzuna</Pill> : <Pill tone="neutral">Sample job</Pill>;
}

/** Which method measured the "meaning" part of the score (see backend/app/semantic.py). */
function engineLabel(engine?: string) {
  if (!engine || engine === "local word overlap") return "word overlap, AI embeddings unavailable";
  return engine.startsWith("gemini") ? "Gemini AI embeddings" : `${engine} embeddings`;
}
