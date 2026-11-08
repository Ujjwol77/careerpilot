"use client";
import { useState } from "react";
import { api, ApiError, useApi } from "@/lib/api";
import { Card, ErrorBox, NeedCv, PageHeader, Pill } from "@/components/ui";
import { LineChart } from "@/components/charts";

/* eslint-disable @typescript-eslint/no-explicit-any */
export default function InterviewPage() {
  const meta = useApi<{ roles: { key: string; label: string }[] }>("/meta");
  const past = useApi<any[]>("/interview/sessions");
  const [role, setRole] = useState("");
  const [session, setSession] = useState<any>(null);
  const [i, setI] = useState(0);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState<Record<number, any>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  async function start() {
    setBusy(true); setError(null);
    try {
      const s = await api("/interview/start", { body: role ? { role } : {} });
      setSession(s); setI(0); setFeedback({}); setAnswer("");
    } catch (e) { setError(e instanceof ApiError ? e : null); }
    finally { setBusy(false); }
  }

  async function submit() {
    setBusy(true); setError(null);
    try {
      const r = await api("/interview/answer", { body: { session_id: session.session_id, index: i, answer } });
      setFeedback({ ...feedback, [i]: r });
      past.reload();
    } catch (e) { setError(e instanceof ApiError ? e : null); }
    finally { setBusy(false); }
  }

  const q = session?.questions[i];
  const fb = feedback[i];
  const last = Object.values(feedback).at(-1) as any;

  return (
    <>
      <PageHeader title="Interview practice" subtitle="The Interview Coach Agent asks role-specific questions and scores your answers." />
      <NeedCv error={error} />
      {!session ? (
        <Card title="Start a session">
          <div className="field"><label htmlFor="r">Role</label>
            <select id="r" value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="">My best-matching role</option>
              {meta.data?.roles.map((r) => <option key={r.key} value={r.key}>{r.label}</option>)}
            </select></div>
          <button className="btn" onClick={start} disabled={busy}>{busy ? "Preparing…" : "Start interview"}</button>
        </Card>
      ) : (
        <Card title={`${session.role_label} · question ${i + 1} of ${session.questions.length}`}>
          <p><Pill tone="brand">{q.type}</Pill><Pill>{q.skill}</Pill></p>
          <p><strong>{q.question}</strong></p>
          <label htmlFor="a">Your answer</label>
          <textarea id="a" value={answer} maxLength={4000} onChange={(e) => setAnswer(e.target.value)} placeholder="For behavioural questions, structure it as Situation, Task, Action, Result." />
          <div className="row" style={{ marginTop: 10 }}>
            <button className="btn" onClick={submit} disabled={busy || !answer.trim()}>{busy ? "Scoring…" : fb ? "Re-score" : "Submit answer"}</button>
            <button className="btn btn-ghost" disabled={i === 0} onClick={() => { setI(i - 1); setAnswer(""); }}>Previous</button>
            <button className="btn btn-ghost" disabled={i >= session.questions.length - 1} onClick={() => { setI(i + 1); setAnswer(""); }}>Next</button>
            <button className="btn btn-ghost" onClick={() => setSession(null)}>End session</button>
          </div>
          <ErrorBox error={null} />
          {fb && (
            <div className="alert alert-good" role="status" style={{ marginTop: 14 }}>
              <strong>Score {fb.score}/10</strong> · session average {fb.average_score} ({fb.answered}/{fb.total} answered)
              <p>{fb.feedback}</p>
              <ul>{fb.tips.map((t: string, k: number) => <li key={k}>{t}</li>)}</ul>
              <span className="small">Feedback source: {fb.feedback_source === "template" ? "rule-based scoring" : fb.feedback_source}</span>
            </div>
          )}
          {last && !fb && <p className="muted small">Last result: {last.score}/10</p>}
        </Card>
      )}
      <Card title="Past sessions">
        {past.data?.filter((s) => s.average_score !== null).length ? (
          <>
            <p className="muted small">Average score per session (out of 10). Hover the line for details.</p>
            <LineChart ariaLabel="Average interview score per session" max={10} unit="/10"
              points={[...past.data].reverse().filter((s) => s.average_score !== null).map((s) => ({ label: new Date(s.created_at).toLocaleDateString(undefined, { day: "numeric", month: "short" }), value: s.average_score }))} />
          </>
        ) : null}
        {past.data?.length ? (
          <table>
            <thead><tr><th>Date</th><th>Role</th><th>Answered</th><th>Average</th></tr></thead>
            <tbody>{past.data.map((s) => (
              <tr key={s.id}><td>{new Date(s.created_at).toLocaleDateString()}</td><td>{s.role.replaceAll("_", " ")}</td><td>{s.answered}/{s.total}</td><td>{s.average_score ?? "-"}</td></tr>
            ))}</tbody>
          </table>
        ) : <p className="muted">No sessions yet.</p>}
      </Card>
    </>
  );
}
