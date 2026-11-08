"use client";
import { useApi } from "@/lib/api";
import { Card, ErrorBox, Loading, PageHeader, Pill } from "@/components/ui";
import { HBarChart } from "@/components/charts";

/* eslint-disable @typescript-eslint/no-explicit-any */
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
                <td><Pill tone={r.status === "ok" ? "good" : "bad"}>{r.status}</Pill></td><td>{r.llm_source || "-"}</td><td className="small">{r.note}</td></tr>
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
