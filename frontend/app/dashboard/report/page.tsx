"use client";
import { useEffect, useState } from "react";
import { api, ApiError, useApi } from "@/lib/api";
import { Card, Loading, NeedCv, PageHeader, Pill, ScoreRing, bandLabel, bandTone } from "@/components/ui";
import { HBarChart } from "@/components/charts";

/* eslint-disable @typescript-eslint/no-explicit-any */
export default function ReportPage() {
  const latest = useApi("/report/latest");
  const [r, setR] = useState<any>(null);
  const [hours, setHours] = useState(8);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  useEffect(() => { if (latest.data) setR(latest.data); }, [latest.data]);

  async function generate() {
    setBusy(true); setError(null);
    try { setR(await api("/report/generate", { body: { hours_per_week: hours } })); }
    catch (e) { setError(e instanceof ApiError ? e : null); }
    finally { setBusy(false); }
  }

  if (latest.loading) return <Loading />;
  return (
    <>
      <PageHeader
        title="Career readiness report"
        subtitle="Runs all seven agents in sequence and combines their output."
        actions={r && <button className="btn btn-ghost" onClick={() => window.print()}>Print / save as PDF</button>}
      />
      <Card className="no-print">
        <div className="row">
          <div style={{ minWidth: 200 }}>
            <label htmlFor="h">Study hours per week: {hours}</label>
            <input id="h" type="range" min={1} max={40} value={hours} onChange={(e) => setHours(Number(e.target.value))} />
          </div>
          <button className="btn" onClick={generate} disabled={busy}>{busy ? "Running agents…" : r ? "Regenerate report" : "Generate report"}</button>
        </div>
      </Card>
      <NeedCv error={error} />
      {r && (
        <>
          <Card>
            <div className="row">
              <ScoreRing value={r.readiness_score} size={96} label="Readiness score" />
              <div>
                <h2 style={{ margin: 0 }}>{r.candidate || "Candidate"} · {r.target_role}</h2>
                <Pill tone={bandTone(r.readiness_band)}>{bandLabel(r.readiness_band)}</Pill>
                <p className="muted small" style={{ margin: 0 }}>Generated {new Date(r.generated_at).toLocaleString()} · summary source: {r.summary_source === "template" ? "built-in template" : r.summary_source}</p>
              </div>
            </div>
            <p style={{ marginTop: 12 }}>{r.summary}</p>
          </Card>

          <Card title="Top job matches">
            <HBarChart ariaLabel="Match score of your top jobs" rows={r.top_jobs.map((j: any) => ({
              label: j.title, value: j.score, display: String(Math.round(j.score)),
              tip: <><strong>{j.title}</strong><br />{j.company}<br />Score {Math.round(j.score)} · {bandLabel(j.readiness)}</>,
            }))} />
            <table style={{ marginTop: 14 }}>
              <thead><tr><th>Role</th><th>Score</th><th>Readiness</th><th>Missing</th></tr></thead>
              <tbody>{r.top_jobs.map((j: any) => (
                <tr key={j.job_id}><td><strong>{j.title}</strong><div className="muted small">{j.company} · {j.location}</div></td><td>{Math.round(j.score)}</td>
                  <td><Pill tone={bandTone(j.readiness)}>{bandLabel(j.readiness)}</Pill></td><td className="small">{j.missing_skills.join(", ") || "-"}</td></tr>
              ))}</tbody>
            </table>
          </Card>

          <div className="grid grid-2">
            <Card title="Skill gaps">
              {r.skill_gaps.missing.length === 0 ? <p className="muted">No gaps found.</p> : (
                <HBarChart ariaLabel="Missing skills by demand" rows={r.skill_gaps.missing.map((s: any) => ({
                  label: s.skill, value: s.demand_pct, display: `${s.demand_pct}%`,
                  color: s.priority === "high" ? "var(--bad)" : s.priority === "medium" ? "var(--warn)" : "var(--s1)",
                  tip: <><strong>{s.skill}</strong><br />Wanted by {s.demand_pct}% of jobs<br /><span className="tip-sub">{s.priority} priority</span></>,
                }))} />
              )}
              <p className="muted small">{r.skill_gaps.experience.advice}</p>
            </Card>
            <Card title="CV">
              <p>ATS score <strong>{r.cv.ats_score}</strong> · keyword coverage {Math.round(r.cv.keyword_coverage * 100)}%</p>
              {r.cv.suggestions.slice(0, 4).map((s: any, i: number) => <p key={i} className="small">• {s.message}</p>)}
            </Card>
          </div>

          <div className="grid grid-2">
            <Card title="Learning plan">
              <p>{r.learning.total_hours} hours · about {r.learning.total_weeks} weeks at {r.learning.hours_per_week} h/week</p>
              <div>{r.learning.focus_skills.map((s: string) => <Pill key={s} tone="brand">{s}</Pill>)}</div>
            </Card>
            <Card title="Interview preparation">
              {r.interview.focus_areas.length > 0 && <p className="small"><strong>Focus:</strong> {r.interview.focus_areas.join(", ")}</p>}
              <ul className="small">{r.interview.schedule.map((s: string, i: number) => <li key={i}>{s}</li>)}</ul>
              <ul className="small">{r.interview.tips.map((s: string, i: number) => <li key={i}>{s}</li>)}</ul>
            </Card>
          </div>

          <Card title="How this report was produced">
            <table>
              <thead><tr><th>Agent</th><th>Result</th><th>Output by</th><th>Time</th></tr></thead>
              <tbody>{r.agent_trace.map((a: any, i: number) => (
                <tr key={i}><td>{a.agent.replaceAll("_", " ")}</td><td className="small">{a.note}</td><td>{a.llm_source}</td><td>{a.duration_ms} ms</td></tr>
              ))}</tbody>
            </table>
          </Card>
        </>
      )}
    </>
  );
}
