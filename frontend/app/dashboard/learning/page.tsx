"use client";
import { useApi } from "@/lib/api";
import { Card, Loading, NeedCv, PageHeader, Pill } from "@/components/ui";

/* eslint-disable @typescript-eslint/no-explicit-any */
const tone = (p: string) => (p === "high" ? "bad" : p === "medium" ? "warn" : "neutral");
const TYPE: Record<string, string> = {
  course: "Course", tutorial: "Tutorial", lab: "Hands-on lab", project: "Project", certification: "Certification",
  practice: "Practice", video: "Video course",
};

export default function LearningPage() {
  const { data, error, loading } = useApi("/learning");
  if (error) return <NeedCv error={error} />;
  // one section per skill gap, in the agent's priority order
  const groups: { skill: string; key: string; priority: string; items: any[] }[] = [];
  for (const it of data?.items ?? []) {
    let g = groups.find((x) => x.skill === it.skill_name);
    if (!g) groups.push(g = { skill: it.skill_name, key: it.skill_name.toLowerCase().replace(/[^a-z0-9]+/g, "-"), priority: it.priority, items: [] });
    g.items.push(it);
  }
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
          {groups.map((g) => (
            <section key={g.skill} className="course-group" aria-labelledby={`gap-${g.key}`}>
              <h2 id={`gap-${g.key}`}>
                {g.skill} <Pill tone={tone(g.priority)}>{g.priority} priority</Pill>
              </h2>
              <div className="course-grid">
                {g.items.map((it: any) => (
                  <article key={it.url} className="course-card">
                    <div className="course-tags">
                      <Pill>{TYPE[it.type] ?? it.type}</Pill>
                      {it.origin === "live" && <Pill tone="good">live</Pill>}
                    </div>
                    <h3><a href={it.url} target="_blank" rel="noopener noreferrer">{it.title}</a></h3>
                    <p className="course-provider">{it.provider}</p>
                    <p className="small course-for">{it.suitable_for}</p>
                    <div className="course-meta">
                      <span>{it.cost === "free" ? "Free" : it.cost[0].toUpperCase() + it.cost.slice(1)}</span>
                      <span>{it.hours_source === "provider" ? "" : "about "}{it.hours} {it.hours === 1 ? "hour" : "hours"}</span>
                      <a className="btn btn-ghost btn-small" href={it.url} target="_blank" rel="noopener noreferrer" aria-label={`Open ${it.title}`}>Open</a>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          ))}
        </>
      )}
    </>
  );
}
