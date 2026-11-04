"use client";
import { useState } from "react";
import { useApi } from "@/lib/api";
import { Card, Loading, NeedCv, PageHeader, Pill } from "@/components/ui";

export default function LearningPage() {
  const [hours, setHours] = useState(8);
  const { data, error, loading } = useApi("/learning", { hours_per_week: hours });
  if (error) return <NeedCv error={error} />;
  return (
    <>
      <PageHeader title="Learning path" subtitle="The Learning Pathway Agent turns your skill gaps into a study schedule." />
      <Card>
        <label htmlFor="h">Hours per week you can study: {hours}</label>
        <input id="h" type="range" min={1} max={40} value={hours} onChange={(e) => setHours(Number(e.target.value))} />
      </Card>
      {loading || !data ? <Loading /> : data.items.length === 0 ? (
        <Card><p className="muted">No gaps to plan for. Nice work.</p></Card>
      ) : (
        <>
          <Card>
            <strong>{data.total_hours} hours</strong> over about <strong>{data.total_weeks} weeks</strong>.
            <div>{data.focus_skills.map((s: string) => <Pill key={s} tone="brand">{s}</Pill>)}</div>
          </Card>
          <Card title="Week by week">
            {data.weeks.map((w: any) => (
              <div className="week" key={w.week}>
                <strong>Week {w.week}</strong>
                {w.items.map((it: any) => (
                  <div key={it.skill + it.title} className="small">
                    <Pill tone={it.priority === "high" ? "bad" : it.priority === "medium" ? "warn" : "neutral"}>{it.type}</Pill>
                    {it.title} <span className="muted">({it.hours}h total, weeks {it.start_week}–{it.end_week})</span>{" "}
                    <a href={`https://www.google.com/search?q=${encodeURIComponent(it.search)}`} target="_blank" rel="noreferrer">Find resources</a>
                  </div>
                ))}
              </div>
            ))}
          </Card>
        </>
      )}
    </>
  );
}
