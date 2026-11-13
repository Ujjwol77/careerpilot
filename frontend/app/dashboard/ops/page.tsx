"use client";
import { useApi } from "@/lib/api";
import { Card, ErrorBox, Loading, PageHeader, Pill, sourceLabel } from "@/components/ui";
import { HBarChart } from "@/components/charts";

/* eslint-disable @typescript-eslint/no-explicit-any */

const SERVICES: Record<string, string> = {
  gemini: "Gemini LLM", embeddings: "Gemini embeddings", adzuna: "Adzuna jobs API",
  mslearn: "Microsoft Learn API", youtube: "YouTube API",
};

/** Which page uses which agent, how the result is produced, and which outside services it depends on. */
const FEATURES: { page: string; agents: string; how: string; services: string[] }[] = [
  { page: "Profile and CV", agents: "Profile Understanding", how: "Rules: skill taxonomy and date parsing for years of experience", services: [] },
  { page: "CV review", agents: "CV Optimisation, with Job Search and Job Matching to pick the target job", how: "Rules for the 12 ATS checks; the LLM writes the rewrite examples", services: ["gemini"] },
  { page: "Jobs and matching", agents: "Job Search, Job Matching", how: "Live postings with sample jobs as fallback; score = 35% meaning (embeddings) + 50% skills + 15% experience", services: ["adzuna", "embeddings"] },
  { page: "Applications", agents: "None", how: "Tracker you update yourself", services: [] },
  { page: "Skill gaps", agents: "Skill Gap", how: "Rules: share of postings for your target role that ask for each skill, tiered core / common / nice to have, ranked by demand and how many jobs a skill would unlock", services: [] },
  { page: "Learning path", agents: "Learning Pathway", how: "Live course search plus a curated catalogue; links always come from the source, never the LLM", services: ["mslearn", "youtube"] },
  { page: "Interview practice", agents: "Interview Coach", how: "Questions from a question bank; the LLM scores and gives feedback on your answers", services: ["gemini"] },
  { page: "Readiness report", agents: "Orchestrator runs all seven agents, then Report", how: "Combines every result into one readiness score; the LLM writes the summary", services: ["gemini", "adzuna", "embeddings"] },
  { page: "Agent monitor", agents: "None", how: "Logs every agent run with status, time and engine", services: [] },
];

export default function OpsPage() {
  const summary = useApi("/ops/summary");
  const runs = useApi<any[]>("/ops/runs");
  const prompts = useApi<any[]>("/prompts");
  if (summary.loading) return <Loading />;
  return (
    <>
      <PageHeader title="Agent monitor" subtitle="LLMOps view: every agent run is logged with status, latency and which engine produced the output."
        actions={<button className="btn btn-ghost" onClick={() => { summary.reload(); runs.reload(); }}>Refresh</button>} />
      <ErrorBox error={summary.error} />
      {summary.data && (
        <Card title="Health">
          <p>LLM provider: <Pill tone={summary.data.llm_provider === "mock" ? "warn" : "good"}>{summary.data.llm_provider}</Pill>
            <span className="muted small"> {summary.data.llm_provider === "mock" ? "Rule-based templates are producing text. Set LLM_PROVIDER in the backend .env to use a real model." : ""}</span></p>
          <p>Job source: <Pill tone={summary.data.job_source === "adzuna" ? "good" : "warn"}>{summary.data.job_source === "adzuna" ? "Adzuna API" : "sample jobs only"}</Pill>
            <span className="muted small"> {summary.data.job_source === "adzuna" ? "Each job search run below shows how many postings came from Adzuna." : "Set ADZUNA_APP_ID and ADZUNA_APP_KEY in the backend .env for live jobs."}</span></p>
          {summary.data.agents.length === 0 ? <p className="muted">No agent runs yet.</p> : (
            <table>
              <thead><tr><th>Agent</th><th>Runs</th><th>Avg latency</th><th>Errors</th></tr></thead>
              <tbody>{summary.data.agents.map((a: any) => (
                <tr key={a.agent}><td>{a.agent.replaceAll("_", " ")}</td><td>{a.runs}</td><td>{a.avg_ms} ms</td><td>{a.errors ? <Pill tone="bad">{a.errors}</Pill> : 0}</td></tr>
              ))}</tbody>
            </table>
          )}
        </Card>
      )}
      {summary.data?.services && (
        <Card title="What each feature uses">
          <p className="small muted">A green service is set up in backend/.env. Set up doesn't guarantee it's working: check each run's note under Recent runs.</p>
          <table>
            <thead><tr><th scope="col">Page</th><th scope="col">Agent(s)</th><th scope="col">How the result is produced</th><th scope="col">External services</th></tr></thead>
            <tbody>{FEATURES.map((f) => (
              <tr key={f.page}>
                <td><strong>{f.page}</strong></td>
                <td>{f.agents}</td>
                <td className="small">{f.how}</td>
                <td>{f.services.length === 0 ? <span className="muted small">None</span> : f.services.map((s) => {
                  const ok = summary.data.services[s]?.set_up;
                  return <Pill key={s} tone={ok ? "good" : "warn"}>{SERVICES[s]}: {ok ? "set up" : "not set up"}</Pill>;
                })}</td>
              </tr>
            ))}</tbody>
          </table>
        </Card>
      )}
      {summary.data?.agents.length > 0 && (
        <div className="grid grid-2">
          <Card title="Runs per agent">
            <HBarChart ariaLabel="Number of runs per agent" max={Math.max(...summary.data.agents.map((a: any) => a.runs), 1)} rows={summary.data.agents.map((a: any) => ({
              label: a.agent.replaceAll("_", " "), value: a.runs, display: String(a.runs),
              tip: <><strong>{a.agent.replaceAll("_", " ")}</strong><br />{a.runs} runs · {a.errors} errors</>,
            }))} />
          </Card>
          <Card title="Average latency (ms)">
            <HBarChart ariaLabel="Average latency per agent in milliseconds" max={Math.max(...summary.data.agents.map((a: any) => a.avg_ms), 1)} rows={summary.data.agents.map((a: any) => ({
              label: a.agent.replaceAll("_", " "), value: a.avg_ms, display: `${a.avg_ms} ms`, color: "var(--s2)",
              tip: <><strong>{a.agent.replaceAll("_", " ")}</strong><br />{a.avg_ms} ms on average</>,
            }))} />
          </Card>
        </div>
      )}
      <Card title="Recent runs">
        {runs.data?.length ? (
          <table>
            <thead><tr><th>When</th><th>Agent</th><th>Status</th><th>Engine</th><th>Note</th></tr></thead>
            <tbody>{runs.data.map((r) => (
              <tr key={r.id}><td className="small">{new Date(r.created_at).toLocaleTimeString()}</td><td>{r.agent.replaceAll("_", " ")}</td>
                <td><Pill tone={r.status === "ok" ? "good" : "bad"}>{r.status}</Pill></td><td>{sourceLabel(r.llm_source)}</td><td className="small">{r.note}</td></tr>
            ))}</tbody>
          </table>
        ) : <p className="muted">No runs yet.</p>}
      </Card>
      <Card title="Prompt bank">
        {prompts.data?.map((p) => (
          <details key={p.id}>
            <summary>{p.id} <Pill tone={p.status === "active" ? "good" : "neutral"}>{p.status}</Pill></summary>
            <p className="small muted">{p.purpose}</p>
            {p.system && <pre>{p.system}</pre>}
            {p.template && <pre>{p.template}</pre>}
          </details>
        ))}
      </Card>
    </>
  );
}
