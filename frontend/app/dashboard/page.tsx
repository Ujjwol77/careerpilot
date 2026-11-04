"use client";
import Link from "next/link";
import { useApi } from "@/lib/api";
import { Card, Loading, PageHeader, Pill, ScoreRing, bandLabel, bandTone } from "@/components/ui";

const AGENTS = [
  ["Profile Understanding", "Reads your CV and extracts skills, experience and education."],
  ["Job Search", "Finds postings that fit your preferences."],
  ["Job Matching", "Scores each posting with semantic similarity, skill coverage and experience fit."],
  ["Skill Gap", "Shows what the best-matching jobs ask for that you do not yet show."],
  ["CV Optimisation", "Checks ATS readiness and suggests honest improvements."],
  ["Learning Pathway", "Turns gaps into a week-by-week study plan."],
  ["Interview Coach", "Generates role-specific questions and scores your answers."],
];

export default function Overview() {
  const profile = useApi("/profile");
  const report = useApi("/report/latest");
  const apps = useApi<unknown[]>("/applications");
  if (profile.loading) return <Loading />;
  const has = profile.data?.has_profile;
  const r = report.data;

  const steps = [
    ["Upload your CV", has, "/dashboard/profile"],
    ["Set job preferences", has && (profile.data.preferences.target_roles.length > 0 || !!profile.data.preferences.location), "/dashboard/profile"],
    ["Review matched jobs", !!r, "/dashboard/jobs"],
    ["Generate your readiness report", !!r, "/dashboard/report"],
    ["Track an application", (apps.data?.length ?? 0) > 0, "/dashboard/applications"],
  ] as const;

  return (
    <>
      <PageHeader title={`Hello${profile.data?.name ? `, ${profile.data.name.split(" ")[0]}` : ""}`} subtitle="Your multi-agent career workspace." />
      <div className="grid grid-2">
        <Card title="Getting started">
          <div className="steps">
            {steps.map(([label, done, href]) => (
              <div className="step" key={label}>
                <span className={`dot ${done ? "done" : ""}`} aria-hidden="true">{done ? "✓" : ""}</span>
                <Link href={href}>{label}</Link>
                {done && <span className="sr-only">(done)</span>}
              </div>
            ))}
          </div>
        </Card>
        <Card title="Latest readiness">
          {r ? (
            <div className="row">
              <ScoreRing value={r.readiness_score} size={84} label="Readiness" />
              <div>
                <Pill tone={bandTone(r.readiness_band)}>{bandLabel(r.readiness_band)}</Pill>
                <p className="muted small">Target: {r.target_role}. <Link href="/dashboard/report">Open report</Link></p>
              </div>
            </div>
          ) : (
            <p className="muted">No report yet. Upload a CV, then generate one from the report page.</p>
          )}
        </Card>
      </div>
      <Card title="The seven agents">
        <div className="grid grid-2">
          {AGENTS.map(([n, d], i) => (
            <div key={n}><strong>{i + 1}. {n}</strong><p className="muted small">{d}</p></div>
          ))}
        </div>
      </Card>
    </>
  );
}
