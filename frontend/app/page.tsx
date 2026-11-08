"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { token } from "@/lib/api";
import { ThemeToggle } from "@/components/ThemeToggle";
import "./landing.css";

/* The route a job seeker takes through CareerPilot, drawn as a flight path (viewBox 640 x 360). */
const STOPS = [
  { x: 40, y: 300, label: "Your CV", place: "below" },
  { x: 140, y: 248, label: "Skills read", place: "above" },
  { x: 240, y: 272, label: "Jobs matched", place: "below" },
  { x: 340, y: 196, label: "Gaps found", place: "above" },
  { x: 440, y: 214, label: "Study plan", place: "below" },
  { x: 530, y: 130, label: "Interview practice", place: "left" },
  { x: 604, y: 66, label: "Job offer", place: "below" },
] as const;

/** Smooth curve through every stop (Catmull-Rom converted to cubic Béziers). */
function routePath(pts: readonly { x: number; y: number }[]) {
  let d = `M${pts[0].x} ${pts[0].y}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] ?? pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] ?? p2;
    const c1 = { x: p1.x + (p2.x - p0.x) / 6, y: p1.y + (p2.y - p0.y) / 6 };
    const c2 = { x: p2.x - (p3.x - p1.x) / 6, y: p2.y - (p3.y - p1.y) / 6 };
    d += ` C${c1.x.toFixed(1)} ${c1.y.toFixed(1)} ${c2.x.toFixed(1)} ${c2.y.toFixed(1)} ${p2.x} ${p2.y}`;
  }
  return d;
}
const ROUTE = routePath(STOPS);
const END = STOPS[STOPS.length - 1];
const PLANE_SCALE = 0.42; // logo plane (120-unit box, nose at 96,24) placed with its nose on the last stop

const AGENTS = [
  ["Profile Understanding", "Reads your CV and lists your skills, experience and education."],
  ["Job Search", "Pulls current Australian postings from Adzuna for the roles you want."],
  ["Job Matching", "Scores every posting out of 100 and shows you why."],
  ["Skill Gap", "Shows which skills your best-matching jobs ask for that your CV doesn't show yet."],
  ["CV Optimisation", "Checks how applicant tracking systems read your CV and suggests honest rewrites."],
  ["Learning Pathway", "Turns your gaps into a week-by-week plan with real courses and videos."],
  ["Interview Coach", "Asks questions for your target role and scores your answers."],
] as const;

export default function Landing() {
  const [signedIn, setSignedIn] = useState(false);
  useEffect(() => setSignedIn(!!token.get()), []);

  return (
    <div className="lp">
      <header className="lp-bar">
        <Link href="/" className="lp-logo"><img src="/logo.svg" alt="" width={30} height={30} /> CareerPilot</Link>
        <nav className="lp-nav" aria-label="Page sections">
          <a href="#route">How it works</a>
          <a href="#agents">The agents</a>
          <a href="#data">Data and scores</a>
        </nav>
        <div className="lp-bar-actions">
          <ThemeToggle />
          {signedIn
            ? <Link className="btn btn-small" href="/dashboard">Open your dashboard</Link>
            : <><Link className="lp-login" href="/login">Log in</Link><Link className="btn btn-small" href="/login?mode=register">Create a free account</Link></>}
        </div>
      </header>

      <main>
        <section className="lp-hero" id="route" aria-labelledby="lp-title">
          <div className="lp-hero-copy">
            <h1 id="lp-title">Plot your course from CV to job offer.</h1>
            <p className="lp-lede">
              Upload your CV and seven AI agents read your skills, match you to live Australian jobs,
              show what you're missing, plan what to study and coach you for the interview.
            </p>
            <div className="lp-ctas">
              {signedIn
                ? <Link className="btn lp-btn-big" href="/dashboard">Open your dashboard</Link>
                : <><Link className="btn lp-btn-big" href="/login?mode=register">Create a free account</Link>
                    <Link className="btn btn-ghost lp-btn-big" href="/login">Log in</Link></>}
            </div>
            <p className="lp-note">Free for job seekers. Your contact details are removed before anything is sent to an AI model.</p>
          </div>

          <figure className="lp-route" aria-label="The CareerPilot route: your CV, skills read, jobs matched, gaps found, study plan, interview practice, job offer">
            <svg viewBox="0 20 640 320" className="lp-route-svg" aria-hidden="true">
              <defs>
                <mask id="lp-draw" maskUnits="userSpaceOnUse">
                  <path d={ROUTE} className="lp-route-reveal" pathLength={1} />
                </mask>
              </defs>
              <path d={ROUTE} className="lp-route-line" mask="url(#lp-draw)" />
              {STOPS.slice(0, -1).map((s, i) => (
                <g key={s.label} className="lp-stop" style={{ animationDelay: `${0.15 + i * 0.22}s` }}>
                  <circle cx={s.x} cy={s.y} r={i === 0 ? 8 : 6} className={i === 0 ? "lp-here" : "lp-dot"} />
                  <text x={s.place === "left" ? s.x - 16 : s.x} y={s.place === "above" ? s.y - 18 : s.place === "left" ? s.y + 5 : s.y + 30}
                    className="lp-stop-label" textAnchor={i === 0 ? "start" : s.place === "left" ? "end" : "middle"} dx={i === 0 ? -8 : 0}>
                    {i + 1}. {s.label}
                  </text>
                </g>
              ))}
              <g className="lp-plane" transform={`translate(${END.x - 96 * PLANE_SCALE} ${END.y - 24 * PLANE_SCALE}) scale(${PLANE_SCALE})`}>
                <polygon points="96,24 46,46 64,55" className="lp-plane-a" />
                <polygon points="96,24 64,55 73,76" className="lp-plane-b" />
              </g>
              <text x={END.x - 34} y={END.y - 10} className="lp-stop-label lp-stop-final" textAnchor="end">7. {END.label}</text>
            </svg>
            <ol className="lp-route-list">
              {STOPS.map((s) => <li key={s.label}>{s.label}</li>)}
            </ol>
          </figure>
        </section>

        <section className="lp-section lp-agents" id="agents" aria-labelledby="lp-agents-title">
          <div className="lp-section-head">
            <h2 id="lp-agents-title">Seven agents, one route</h2>
            <p>Each agent does one job and hands its result to the next. An orchestrator runs them in order, and widens the search on its own when too few jobs fit.</p>
          </div>
          <ol className="lp-agent-list">
            {AGENTS.map(([name, what]) => (
              <li key={name}><strong>{name}</strong><span>{what}</span></li>
            ))}
          </ol>
        </section>

        <section className="lp-section" id="data" aria-labelledby="lp-data-title">
          <h2 id="lp-data-title">Built on real data you can check</h2>
          <div className="lp-facts">
            <div>
              <h3>Live jobs</h3>
              <p>Current postings from Adzuna, refreshed every 12 hours. Every job links to the real advert, and sample jobs are clearly labelled.</p>
            </div>
            <div>
              <h3>Real courses</h3>
              <p>Microsoft Learn modules, full YouTube courses and a hand-checked list of free providers. Every link opens a real course page.</p>
            </div>
            <div>
              <h3>Scores that show their working</h3>
              <p>A match score is 50% skills you have, 35% how closely your CV reads like the advert and 15% experience. AI writes your feedback; it never sets your score.</p>
            </div>
          </div>
        </section>

        <section className="lp-close" aria-labelledby="lp-close-title">
          <h2 id="lp-close-title">Start with your CV.</h2>
          <p>A PDF or Word file is enough. Your first readiness report is a few clicks away.</p>
          {signedIn
            ? <Link className="btn lp-btn-big" href="/dashboard">Open your dashboard</Link>
            : <Link className="btn lp-btn-big" href="/login?mode=register">Create a free account</Link>}
        </section>
      </main>

      <footer className="lp-foot">
        <p>CareerPilot is a NIT 3004 IT capstone student project by Agrata Shrestha and Ujjwol Adhikari from Victora University.</p>
        <p>Job listings by <a href="https://www.adzuna.com.au" target="_blank" rel="noopener noreferrer">Adzuna</a>.</p>
      </footer>
    </div>
  );
}
