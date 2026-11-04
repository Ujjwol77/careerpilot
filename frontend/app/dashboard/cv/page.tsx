"use client";
import { useState } from "react";
import { useApi } from "@/lib/api";
import { Card, Loading, NeedCv, PageHeader, Pill, ScoreRing } from "@/components/ui";

const tone = (s: string) => (s === "high" ? "bad" : s === "medium" ? "warn" : "neutral");

export default function CvPage() {
  const jobs = useApi<{ jobs: { id: number; title: string; company: string }[] }>("/jobs/search");
  const [jobId, setJobId] = useState("");
  const { data, error, loading } = useApi("/cv/optimise", { job_id: jobId });
  if (error) return <NeedCv error={error} />;
  return (
    <>
      <PageHeader title="CV review" subtitle="The CV Optimisation Agent checks ATS readiness. It only suggests changes you can honestly make." />
      <Card>
        <label htmlFor="job">Tailor the review to a job</label>
        <select id="job" value={jobId} onChange={(e) => setJobId(e.target.value)}>
          <option value="">My best match</option>
          {jobs.data?.jobs.map((j) => <option key={j.id} value={j.id}>{j.title} · {j.company}</option>)}
        </select>
      </Card>
      {loading || !data ? <Loading /> : (
        <>
          <div className="grid grid-2">
            <Card title="ATS readiness">
              <div className="row">
                <ScoreRing value={data.ats_score} size={84} label="ATS score" />
                <div>
                  <p className="small muted">Target: {data.target_job?.title ?? "general"} {data.target_job && `at ${data.target_job.company}`}</p>
                  <p className="small">{data.word_count} words · {data.bullet_count} bullet points · {Math.round(data.keyword_coverage * 100)}% keyword coverage</p>
                </div>
              </div>
            </Card>
            <Card title="Keywords the job wants that your CV lacks">
              {data.missing_keywords.length === 0 ? <p className="muted">None. Your CV already covers the key terms.</p>
                : <div>{data.missing_keywords.map((k: string) => <Pill key={k} tone="warn">{k}</Pill>)}</div>}
              {data.missing_keywords.length > 0 && <p className="muted small">Add these only if you genuinely have the skill.</p>}
            </Card>
          </div>
          <Card title="Suggestions">
            {data.suggestions.length === 0 && <p className="muted">No issues found.</p>}
            {data.suggestions.map((s: any, i: number) => (
              <p key={i}><Pill tone={tone(s.severity)}>{s.area}</Pill> {s.message}</p>
            ))}
          </Card>
          {data.rewrite_examples.length > 0 && (
            <Card title="Rewrite examples">
              <p className="muted small">Source: {data.rewrite_source === "template" ? "built-in templates" : data.rewrite_source}</p>
              {data.rewrite_examples.map((r: string, i: number) => <pre key={i}>{r}</pre>)}
            </Card>
          )}
        </>
      )}
    </>
  );
}
