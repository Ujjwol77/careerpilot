"use client";
import { Fragment, useState } from "react";
import { useApi } from "@/lib/api";
import { Card, Loading, NeedCv, PageHeader, Pill, ScoreRing, bandLabel, bandTone } from "@/components/ui";
import "./cv.css";

const tone = (s: string) => (s === "high" ? "bad" : s === "medium" ? "warn" : "neutral");
const ordinal = (n: number) => `${n}${["th", "st", "nd", "rd"][((n % 100) - 20) % 10] || ["th", "st", "nd", "rd"][n % 100] || "th"}`;
const pts = (n: number) => (Number.isInteger(n) ? `${n}` : n.toFixed(1));

const COMPONENTS = [
  { key: "skill_coverage", label: "Skills the advert asks for that your CV shows" },
  { key: "semantic", label: "How closely your CV's meaning matches the advert" },
  { key: "experience_fit", label: "Your years of experience vs the role's level" },
] as const;

/** Highlights [placeholders] the user must fill in with their own facts. */
function WithPlaceholders({ text }: { text: string }) {
  const parts = text.split(/(\[[^\]]+\])/g);
  return <>{parts.map((p, i) => (p.startsWith("[") ? <mark key={i} className="cv-fill">{p}</mark> : <Fragment key={i}>{p}</Fragment>))}</>;
}

function CopyButton({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <button type="button" className="btn btn-ghost btn-small"
      onClick={() => { navigator.clipboard?.writeText(text).then(() => { setDone(true); setTimeout(() => setDone(false), 1500); }); }}>
      {done ? "Copied" : "Copy"}
    </button>
  );
}

export default function CvPage() {
  const jobs = useApi<{ jobs: { id: number; title: string; company: string }[] }>("/jobs/search");
  const [jobId, setJobId] = useState("");
  const { data, error, loading } = useApi("/cv/optimise", { job_id: jobId });
  if (error) return <NeedCv error={error} />;
  const reason = data?.target_reason;

  return (
    <>
      <PageHeader title="CV review" subtitle="The CV Optimisation Agent checks how applicant tracking systems (ATS) and recruiters will read your CV. It only suggests changes you can honestly make." />
      <Card>
        <label htmlFor="job">Tailor the review to a job</label>
        <select id="job" value={jobId} onChange={(e) => setJobId(e.target.value)}>
          <option value="">My best match</option>
          {jobs.data?.jobs.map((j) => <option key={j.id} value={j.id}>{j.title} · {j.company}</option>)}
        </select>

        {reason && data.target_job && (
          <div className="cv-why-job">
            <p>
              {reason.mode === "best_match" ? "Reviewing against " : "You chose "}
              <strong>{data.target_job.title}</strong> at {data.target_job.company}
              {reason.mode === "best_match"
                ? <> because it is your highest-scoring match: <strong>{pts(reason.score)}/100</strong>, ranked 1st of your {reason.of} matches.</>
                : reason.rank
                  ? <>. It ranks {ordinal(reason.rank)} of your {reason.of} matches with <strong>{pts(reason.score)}/100</strong>.</>
                  : <>. It is outside your top {reason.of} matches and scores <strong>{pts(reason.score)}/100</strong> for your CV.</>}
              {" "}<Pill tone={bandTone(reason.readiness)}>{bandLabel(reason.readiness)}</Pill>
            </p>
            <table className="cv-table">
              <caption className="sr-only">How the match score for this job is calculated</caption>
              <thead><tr><th scope="col">Part of the match score</th><th scope="col">Weight</th><th scope="col">Your result</th><th scope="col">Points</th></tr></thead>
              <tbody>
                {COMPONENTS.map(({ key, label }) => {
                  const w = reason.weights[key], v = reason.components[key];
                  return (
                    <tr key={key}>
                      <td>{label}</td>
                      <td>{Math.round(w * 100)}%</td>
                      <td>{Math.round(v * 100)}%</td>
                      <td>{(w * v * 100).toFixed(1)}</td>
                    </tr>
                  );
                })}
                <tr className="cv-total"><td colSpan={3}>Match score</td><td>{pts(reason.score)}</td></tr>
              </tbody>
            </table>
            <p className="small muted">
              {reason.semantic_engine && reason.semantic_engine !== "local word overlap"
                ? `Meaning is measured by an AI embedding model (${reason.semantic_engine}), which compares what your CV and the advert are about, not just shared words.`
                : "Meaning is measured by word overlap because the AI embedding model is unavailable; this is less accurate."}
            </p>
            {reason.missing_skills.length > 0 && (
              <p className="small muted">Skills from this advert not found in your CV: {reason.missing_skills.join(", ")}.</p>
            )}
            {reason.runners_up.length > 0 && (
              <p className="small cv-runners">
                {reason.mode === "best_match" ? "Next best: " : "Your top matches: "}
                {reason.runners_up.map((r: any, i: number) => (
                  <Fragment key={r.job_id}>
                    {i > 0 && ", "}
                    <button type="button" className="cv-linkbtn" onClick={() => setJobId(String(r.job_id))}>{r.title} at {r.company} ({pts(r.score)})</button>
                  </Fragment>
                ))}
              </p>
            )}
          </div>
        )}
      </Card>

      {loading || !data ? <Loading /> : (
        <>
          <div className="grid grid-2">
            <Card title="ATS readiness">
              <div className="row">
                <ScoreRing value={data.ats_score} size={84} label="ATS score" />
                <div>
                  <p className="small">{data.score_breakdown.passed} of {data.score_breakdown.total_checks} checks passed</p>
                  <p className="small muted">{data.word_count} words, {data.bullet_count} bullet points, {Math.round(data.keyword_coverage * 100)}% of the advert's keywords</p>
                </div>
              </div>
              <div className="cv-sum" aria-label="How the ATS score is calculated">
                <span>Start</span><span className="cv-sum-n">100</span>
                {data.score_breakdown.deductions.map((d: any) => (
                  <Fragment key={d.check}><span>{d.check}</span><span className="cv-sum-n cv-minus">−{pts(d.points)}</span></Fragment>
                ))}
                <span className="cv-sum-total">ATS score</span><span className="cv-sum-n cv-sum-total">{data.ats_score}</span>
              </div>
            </Card>
            <Card title="Keywords the job wants that your CV lacks">
              {data.missing_keywords.length === 0 ? <p className="muted">None. Your CV already mentions every technical skill and tool in this advert.</p>
                : <div>{data.missing_keywords.map((k: string) => <Pill key={k} tone="warn">{k}</Pill>)}</div>}
              {data.missing_keywords.length > 0 && <p className="muted small">Add these only if you genuinely have the skill. Otherwise they're in your Learning plan.</p>}
            </Card>
          </div>

          <Card title="Suggestions, biggest gain first">
            {data.suggestions.length === 0 && <p className="muted">Every check passed. Nothing to fix for this job.</p>}
            <ol className="cv-suggestions">
              {data.suggestions.map((s: any) => (
                <li key={s.check}>
                  <div className="cv-sug-head">
                    <span className="cv-gain">+{pts(s.points)} points</span>
                    <strong>{s.check}</strong>
                    <Pill tone={tone(s.severity)}>{s.severity} priority</Pill>
                  </div>
                  <p>{s.message}</p>
                  <p className="small cv-measure">Your CV: <strong>{s.found}</strong>. Target: <strong>{s.target}</strong>.</p>
                  <p className="small muted">Why it matters: {s.why}</p>
                </li>
              ))}
            </ol>
            <p className="small muted">Ranked by the points each fix would add to your ATS score. Fixing all of them would take you to {Math.min(100, data.ats_score + Math.round(data.suggestions.reduce((t: number, s: any) => t + s.points, 0)))}.</p>
          </Card>

          <Card title="Every check we ran">
            <table className="cv-table">
              <caption className="sr-only">All ATS checks with your result and the target</caption>
              <thead><tr><th scope="col">Check</th><th scope="col">Your CV</th><th scope="col">Target</th><th scope="col">Result</th></tr></thead>
              <tbody>
                {data.checks.map((c: any) => (
                  <tr key={c.id}>
                    <td>{c.label}</td>
                    <td>{c.found}</td>
                    <td>{c.target}</td>
                    <td>{c.passed ? <span className="cv-pass">Passed</span> : <span className="cv-fail">−{pts(c.points_lost)} of {c.max_points}</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          {data.rewrites?.length > 0 && (
            <Card title="Rewrite examples">
              <p className="small muted">
                {data.rewrite_source === "llm" ? "Written by the AI model from your own bullets." : "Templates based on your own bullets."}{" "}
                Highlighted parts are placeholders: replace them with your real numbers, or leave them out.
              </p>
              <div className="cv-rewrites">
                {data.rewrites.map((r: any, i: number) => (
                  <article key={i} className="cv-rewrite">
                    <div className="cv-before">
                      <h3>Before</h3>
                      <p className="cv-doc">{r.before}</p>
                      <p className="small muted">Chosen because it {r.why.join(" and ")}.</p>
                    </div>
                    <div className="cv-after">
                      <h3>After</h3>
                      <p className="cv-doc"><WithPlaceholders text={r.after} /></p>
                      <CopyButton text={r.after} />
                    </div>
                  </article>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </>
  );
}
