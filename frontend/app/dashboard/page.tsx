"use client";
import Link from "next/link";
import { useApi } from "@/lib/api";
import { Card, Loading, PageHeader, Pill, ScoreRing, bandLabel, bandTone } from "@/components/ui";
import { Donut, HBarChart, Kpi, Radar, type Slice } from "@/components/charts";

/* eslint-disable @typescript-eslint/no-explicit-any */
const CATS = [["technical", "Technical"], ["tool", "Tools"], ["soft", "Soft skills"], ["certification", "Certifications"]] as const;
const STATUS: [string, string][] = [["saved", "var(--s1)"], ["applied", "var(--s2)"], ["interview", "var(--s3)"], ["offer", "var(--good)"], ["rejected", "var(--bad)"]];

export default function Overview() {
  const profile = useApi("/profile");
  const report = useApi("/report/latest");
  const apps = useApi<any[]>("/applications");
  if (profile.loading) return <Loading />;
  const has = profile.data?.has_profile;
  const r = report.data;
  const skills: any[] = profile.data?.skills ?? [];
  const missing: any[] = r?.skill_gaps?.missing ?? [];

  const coverage = CATS.map(([key, label]) => {
    const have = skills.filter((s) => s.category === key).length;
    const gaps = missing.filter((m) => m.category === key).length;
    return { label, have, gaps, total: have + gaps };
  }).filter((c) => c.total > 0);

  const pipeline: Slice[] = STATUS.map(([s, color]) => ({ label: s, color, value: apps.data?.filter((a) => a.status === s).length ?? 0 })).filter((s) => s.value > 0);

  const steps = [
    ["Upload your CV", has, "/dashboard/profile"],
    ["Review matched jobs", !!r, "/dashboard/jobs"],
    ["Generate your readiness report", !!r, "/dashboard/report"],
    ["Track an application", (apps.data?.length ?? 0) > 0, "/dashboard/applications"],
  ] as const;

  return (
    <>
      <PageHeader title={`Hello${profile.data?.name ? `, ${profile.data.name.split(" ")[0]}` : ""}`} subtitle="Your career workspace at a glance. Hover any chart for details." />

      <div className="kpis">
        <Kpi label="Readiness score" value={r ? r.readiness_score : null} decimals={0} suffix="/100" hint={r ? bandLabel(r.readiness_band) : "Generate a report"} accent="var(--s1)" />
        <Kpi label="Skills detected" value={has ? skills.length : null} hint="from your CV" accent="var(--s3)" />
        <Kpi label="Years of experience" value={has ? profile.data.years_experience : null} decimals={1} hint="estimated from your CV" accent="var(--s2)" />
        <Kpi label="Applications tracked" value={apps.data ? apps.data.length : null} hint="across all stages" accent="var(--s4)" />
      </div>

      <div className="grid grid-2">
        <Card title="Top job matches">
          {r ? (
            <>
              <HBarChart ariaLabel="Match score of your top jobs" rows={r.top_jobs.map((j: any) => ({
                label: j.title, value: j.score, display: String(Math.round(j.score)),
                tip: <><strong>{j.title}</strong><br />{j.company}<br />Score {Math.round(j.score)} · {bandLabel(j.readiness)}{j.missing_skills.length ? <><br /><span className="tip-sub">Missing: {j.missing_skills.join(", ")}</span></> : null}</>,
              }))} />
              <p className="small muted" style={{ marginTop: 8 }}><Link href="/dashboard/jobs">See all matches</Link></p>
            </>
          ) : <p className="muted">Generate a readiness report to see your best matches here.</p>}
        </Card>

        <Card title="Skill coverage by type">
          {coverage.length >= 3 ? (
            <Radar ariaLabel="Share of wanted skills you already have, by skill type" axes={coverage.map((c) => ({
              label: c.label, value: (c.have / c.total) * 100,
              tip: <><strong>{c.label}</strong><br />You have {c.have} of {c.total} wanted<br /><span className="tip-sub">{c.gaps} still missing</span></>,
            }))} />
          ) : coverage.length > 0 ? (
            <HBarChart ariaLabel="Skill coverage by type" rows={coverage.map((c) => ({ label: c.label, value: (c.have / c.total) * 100, display: `${c.have}/${c.total}` }))} />
          ) : <p className="muted">Coverage appears once you have a profile and a report.</p>}
        </Card>

        <Card title="Application pipeline">
          {pipeline.length ? (
            <Donut ariaLabel="Applications by stage" slices={pipeline} centerValue={String(apps.data?.length ?? 0)} centerLabel="tracked" />
          ) : <p className="muted">Nothing tracked yet. Use Track on any job to start your pipeline.</p>}
        </Card>

        <Card title="Latest readiness">
          {r ? (
            <div className="row">
              <ScoreRing value={r.readiness_score} size={96} label="Readiness" />
              <div>
                <Pill tone={bandTone(r.readiness_band)}>{bandLabel(r.readiness_band)}</Pill>
                <p className="muted small">Target: {r.target_role}.</p>
                <Link href="/dashboard/report">Open the full report</Link>
              </div>
            </div>
          ) : (
            <div className="steps">
              {steps.map(([label, done, href]) => (
                <div className="step" key={label}>
                  <span className={`dot ${done ? "done" : ""}`} aria-hidden="true">{done ? "✓" : ""}</span>
                  <Link href={href}>{label}</Link>
                  {done && <span className="sr-only">(done)</span>}
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </>
  );
}
