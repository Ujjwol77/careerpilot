"use client";
import { useApi } from "@/lib/api";
import { Card, Loading, NeedCv, PageHeader } from "@/components/ui";
import { HBarChart, Legend, Radar } from "@/components/charts";

/* eslint-disable @typescript-eslint/no-explicit-any */
const CATS = [["technical", "Technical"], ["tool", "Tools"], ["soft", "Soft skills"], ["certification", "Certifications"]] as const;
const color = (p: string) => (p === "high" ? "var(--bad)" : p === "medium" ? "var(--warn)" : "var(--s1)");

export default function SkillsPage() {
  const { data, error, loading } = useApi("/skill-gap");
  const profile = useApi("/profile");
  if (loading) return <Loading text="The Skill Gap Agent is comparing you with top jobs…" />;
  if (error) return <NeedCv error={error} />;
  const d = data;
  const skills: any[] = profile.data?.skills ?? [];
  const coverage = CATS.map(([key, label]) => {
    const have = skills.filter((s) => s.category === key).length;
    const gaps = d.missing.filter((m: any) => m.category === key).length;
    return { label, have, gaps, total: have + gaps };
  }).filter((c) => c.total > 0);

  return (
    <>
      <PageHeader title="Skill gaps" subtitle={`Compared with your ${d.jobs_analysed} best-matching jobs. Demand is the share of those jobs asking for the skill. Hover a bar for details.`} />
      <div className="grid grid-2">
        <Card title="Coverage by skill type">
          {coverage.length >= 3 ? (
            <Radar ariaLabel="Share of wanted skills you already have, by skill type" axes={coverage.map((c) => ({
              label: c.label, value: (c.have / c.total) * 100,
              tip: <><strong>{c.label}</strong><br />You have {c.have} of {c.total} wanted<br /><span className="tip-sub">{c.gaps} still missing</span></>,
            }))} />
          ) : <p className="muted">Not enough skill types to draw a chart yet.</p>}
        </Card>
        <Card title="Experience">
          <p>{d.experience.advice}</p>
          <HBarChart ariaLabel="Your years of experience against the typical requirement" max={Math.max(d.experience.your_years, d.experience.typical_required_years, 1)} rows={[
            { label: "You", value: d.experience.your_years, display: `${d.experience.your_years} yrs`, color: "var(--s3)" },
            { label: "Typical requirement", value: d.experience.typical_required_years, display: `${d.experience.typical_required_years} yrs`, color: "var(--s2)" },
          ]} />
        </Card>
      </div>

      <div className="grid grid-2">
        <Card title="Gaps to close">
          {d.missing.length === 0 ? <p className="muted">No gaps found against these jobs.</p> : (
            <>
              <Legend items={[{ label: "High priority", color: "var(--bad)" }, { label: "Medium", color: "var(--warn)" }, { label: "Low", color: "var(--s1)" }]} />
              <HBarChart ariaLabel="Missing skills by demand" rows={d.missing.map((s: any) => ({
                label: s.skill, value: s.demand_pct, display: `${s.demand_pct}%`, color: color(s.priority),
                tip: <><strong>{s.skill}</strong><br />Wanted by {s.demand_pct}% of jobs<br /><span className="tip-sub">{s.category} · {s.priority} priority</span></>,
              }))} />
            </>
          )}
        </Card>
        <Card title="Your strengths">
          {d.strengths.length === 0 ? <p className="muted">Strengths appear once your skills overlap with job requirements.</p> : (
            <HBarChart ariaLabel="Your skills that jobs ask for" rows={d.strengths.map((s: any) => ({
              label: s.skill, value: s.demand_pct, display: `${s.demand_pct}%`, color: "var(--good)",
              tip: <><strong>{s.skill}</strong><br />You have it, and {s.demand_pct}% of jobs want it</>,
            }))} />
          )}
        </Card>
      </div>
    </>
  );
}
