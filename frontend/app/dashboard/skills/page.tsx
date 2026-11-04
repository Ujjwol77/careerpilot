"use client";
import { useApi } from "@/lib/api";
import { Bar, Card, Loading, NeedCv, PageHeader, Pill } from "@/components/ui";

const tone = (p: string) => (p === "high" ? "bad" : p === "medium" ? "warn" : "neutral");

export default function SkillsPage() {
  const { data, error, loading } = useApi("/skill-gap");
  if (loading) return <Loading text="The Skill Gap Agent is comparing you with top jobs…" />;
  if (error) return <NeedCv error={error} />;
  const d = data;
  return (
    <>
      <PageHeader title="Skill gaps" subtitle={`Compared with your ${d.jobs_analysed} best-matching jobs. Demand is the share of those jobs asking for the skill.`} />
      <Card title="Experience">
        <p>{d.experience.advice}</p>
        <p className="muted small">You: {d.experience.your_years} years · typical requirement: {d.experience.typical_required_years} years</p>
      </Card>
      <div className="grid grid-2">
        <Card title="Gaps to close">
          {d.missing.length === 0 && <p className="muted">No gaps found against these jobs.</p>}
          {Object.entries(d.grouped as Record<string, any[]>).map(([group, items]) => items.length > 0 && (
            <div key={group}>
              <h3>{group}</h3>
              {items.map((s) => (
                <div key={s.slug} style={{ marginBottom: 10 }}>
                  <div className="spread"><span>{s.skill}</span><Pill tone={tone(s.priority)}>{s.priority} priority</Pill></div>
                  <Bar value={s.demand_pct} tone={s.priority === "high" ? "bad" : s.priority === "medium" ? "warn" : "brand"} />
                  <span className="muted small">{s.demand_pct}% of jobs</span>
                </div>
              ))}
            </div>
          ))}
        </Card>
        <Card title="Your strengths">
          {d.strengths.length === 0 && <p className="muted">Strengths appear once your skills overlap with job requirements.</p>}
          {d.strengths.map((s: any) => (
            <div key={s.skill} style={{ marginBottom: 10 }}>
              <div className="spread"><span>{s.skill}</span><span className="muted small">{s.demand_pct}% of jobs</span></div>
              <Bar value={s.demand_pct} tone="good" />
            </div>
          ))}
        </Card>
      </div>
    </>
  );
}
