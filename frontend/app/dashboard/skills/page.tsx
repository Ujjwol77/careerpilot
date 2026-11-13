"use client";
import { useApi } from "@/lib/api";
import { Card, Loading, NeedCv, PageHeader, Pill } from "@/components/ui";
import { InfoTip } from "@/components/InfoTip";
import { HBarChart, Kpi, Legend, Radar } from "@/components/charts";

/* eslint-disable @typescript-eslint/no-explicit-any */
const color = (p: string) => (p === "high" ? "var(--bad)" : p === "medium" ? "var(--warn)" : "var(--s1)");
const TIER: Record<string, string> = { core: "Core for this role", common: "Common", nice_to_have: "Nice to have" };

export default function SkillsPage() {
  const { data, error, loading } = useApi("/skill-gap");
  if (loading) return <Loading text="The Skill Gap Agent is comparing you with the role…" />;
  if (error) return <NeedCv error={error} />;
  const d = data;

  return (
    <>
      <PageHeader title="Skill gaps" subtitle={`Compared with ${d.jobs_analysed} ${d.role} postings. Demand is the share of those postings asking for a skill.`} />

      <Card>
        <div className="row">
          <Kpi label="Of the role's demand you already cover" value={d.overall_coverage_pct} decimals={0} suffix="%" accent="var(--s1)" />
          <div style={{ flex: 1, minWidth: 240 }}>
            <p style={{ margin: "0 0 6px" }}><strong>{d.headline}</strong></p>
            <p className="small" style={{ margin: 0 }}><strong>Next step:</strong> {d.next_step}</p>
            {d.quick_wins.length > 0 && <p className="small muted" style={{ margin: "6px 0 0" }}>Quick wins (first course under 8 hours): {d.quick_wins.join(", ")}.</p>}
          </div>
        </div>
        {d.confidence.level === "low" && <p className="small muted" role="note" style={{ marginBottom: 0 }}>Low confidence: {d.confidence.note}</p>}
      </Card>

      <div className="grid grid-2">
        <Card title="How much of each skill type you cover" info="Each skill counts by how often postings ask for it, so missing a skill everyone wants costs more than missing a rare one.">
          {d.coverage.length >= 3 ? (
            <Radar ariaLabel="Share of the demand in each skill type that you already cover" axes={d.coverage.map((c: any) => ({
              label: c.label, value: c.coverage_pct,
              tip: <><strong>{c.label}</strong><br />You have {c.have} of the {c.wanted} skills asked for<br /><span className="tip-sub">{c.coverage_pct}% of demand covered</span></>,
            }))} />
          ) : d.coverage.length > 0 ? (
            <HBarChart ariaLabel="Share of the demand in each skill type that you already cover" max={100} rows={d.coverage.map((c: any) => ({
              label: c.label, value: c.coverage_pct, display: `${c.coverage_pct}%`, color: "var(--s1)",
              tip: <><strong>{c.label}</strong><br />You have {c.have} of the {c.wanted} skills asked for</>,
            }))} />
          ) : <p className="muted">No skill demand found yet.</p>}
        </Card>
        <Card title="Experience">
          <p>{d.experience.advice}</p>
          <HBarChart ariaLabel="Your years of experience against the typical requirement" max={Math.max(d.experience.your_years, d.experience.range[1], 1)} rows={[
            { label: "You", value: d.experience.your_years, display: `${d.experience.your_years} yrs`, color: "var(--s3)" },
            { label: "Typical (median)", value: d.experience.typical_required_years, display: `${d.experience.typical_required_years} yrs`, color: "var(--s2)" },
            { label: "Most demanding", value: d.experience.range[1], display: `${d.experience.range[1]} yrs`, color: "var(--s4)" },
          ]} />
          <p className="muted small">You meet the experience asked for in {d.experience.meets_pct}% of these postings.</p>
        </Card>
      </div>

      <Card title="Gaps to close, in the order to tackle them" info="Priority comes from demand and skill type, and goes up one level when closing a skill completes your list for 2 or more postings.">
        {d.missing.length === 0 ? <p className="muted">No gaps found against these postings.</p> : (
          <>
            <Legend items={[{ label: "High priority", color: "var(--bad)" }, { label: "Medium", color: "var(--warn)" }, { label: "Low", color: "var(--s1)" }]} />
            {d.missing.slice(0, 12).map((s: any) => (
              <div className="job" key={s.slug}>
                <div className="job-body">
                  <div className="spread">
                    <div>
                      <strong>{s.skill}</strong>{" "}
                      <Pill tone={s.priority === "high" ? "bad" : s.priority === "medium" ? "warn" : "neutral"}>{s.priority} priority</Pill>{" "}
                      <Pill>{TIER[s.tier]}</Pill>
                      {s.quick_win && <Pill tone="good">quick win</Pill>}
                      <InfoTip label={`Why ${s.skill} is a gap`}>{s.why}</InfoTip>
                    </div>
                  </div>
                  <HBarChart ariaLabel={`${s.skill} demand`} max={100} rows={[{ label: "Demand", value: s.demand_pct, display: `${s.demand_pct}%`, color: color(s.priority),
                    tip: <><strong>{s.skill}</strong><br />Asked for by {s.jobs_asking} of {d.jobs_analysed} postings</> }]} />
                </div>
              </div>
            ))}
            {d.missing.length > 12 && <p className="muted small">Plus {d.missing.length - 12} lower-demand skills not shown.</p>}
          </>
        )}
      </Card>

      <div className="grid grid-2">
        <Card title="Your strengths">
          {d.strengths.length === 0 ? <p className="muted">Strengths appear once your skills overlap with what postings ask for.</p> : (
            <HBarChart ariaLabel="Your skills that postings ask for" max={100} rows={d.strengths.map((s: any) => ({
              label: s.skill, value: s.demand_pct, display: `${s.demand_pct}%`, color: "var(--good)",
              tip: <><strong>{s.skill}</strong><br />You have it, and {s.demand_pct}% of postings want it</>,
            }))} />
          )}
        </Card>
        <Card title="Other skills you have" info="Not asked for in these postings, but they can set you apart. Mention them if they are relevant to the job.">
          {d.extras.length === 0 ? <p className="muted">Every skill on your CV is asked for by this role.</p> : (
            <>
              <div>{d.extras.map((s: string) => <Pill key={s}>{s}</Pill>)}</div>
            </>
          )}
        </Card>
      </div>
    </>
  );
}
