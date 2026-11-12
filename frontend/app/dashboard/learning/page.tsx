"use client";
import { useApi } from "@/lib/api";
import { Card, Loading, NeedCv, PageHeader, Pill } from "@/components/ui";

/* eslint-disable @typescript-eslint/no-explicit-any */
export default function LearningPage() {
  const { data, error, loading } = useApi("/learning");
  if (error) return <NeedCv error={error} />;
  return (
    <>
      <PageHeader title="Learning path" subtitle="Courses recommended by the Learning Pathway Agent to close your skill gaps." />
      {loading || !data ? <Loading /> : data.items.length === 0 ? (
        <Card><p className="muted">No gaps to plan for. Nice work.</p></Card>
      ) : (
        <>
          <Card>
            <strong>{data.items.length} recommended courses</strong> for:
            <div>{data.focus_skills.map((s: string) => <Pill key={s} tone="brand">{s}</Pill>)}</div>
            <p className="muted small">
              {data.live_sources?.length
                ? `Live results from ${data.live_sources.join(" and ")}, plus one curated pick per skill.`
                : "Showing the curated course catalogue."}
            </p>
          </Card>
          <Card title="Recommended courses">
            {data.items.map((it: any) => (
              <div className="week" key={it.skill_name + it.url}>
                <div className="small">
                  <Pill tone={it.priority === "high" ? "bad" : it.priority === "medium" ? "warn" : "neutral"}>{it.type}</Pill>
                  <a href={it.url} target="_blank" rel="noopener noreferrer"><strong>{it.title}</strong></a>{" "}
                  {it.origin === "live" && <Pill tone="good">live</Pill>}{" "}
                  <span className="muted">· {it.provider} · {it.cost} · {it.hours_source === "provider" ? "" : "~"}{it.hours}h</span>
                </div>
                <div className="small muted"><strong>For:</strong> {it.suitable_for}</div>
                <div className="small muted">Closes your gap in {it.skill_name}</div>
              </div>
            ))}
          </Card>
        </>
      )}
    </>
  );
}
