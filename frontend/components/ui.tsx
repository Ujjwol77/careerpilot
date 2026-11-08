import Link from "next/link";
import type { ReactNode } from "react";
import type { ApiError } from "@/lib/api";

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <header className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {actions && <div className="no-print row">{actions}</div>}
    </header>
  );
}

export function Card({ title, children, className = "" }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`card ${className}`}>
      {title && <h2>{title}</h2>}
      {children}
    </section>
  );
}

export function Pill({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "good" | "warn" | "bad" | "brand" }) {
  return <span className={`pill pill-${tone}`}>{children}</span>;
}

export const bandTone = (band: string) => (band === "HIGHLY_QUALIFIED" ? "good" : band === "QUALIFIED_WITH_GAPS" ? "warn" : "bad");
export const bandLabel = (band: string) => band.replaceAll("_", " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());

export function ScoreRing({ value, size = 64, label }: { value: number; size?: number; label?: string }) {
  const r = (size - 8) / 2;
  const c = 2 * Math.PI * r;
  const tone = value >= 80 ? "var(--good)" : value >= 60 ? "var(--warn)" : "var(--bad)";
  return (
    <div className="ring" style={{ width: size, height: size }} role="img" aria-label={`${label ?? "Score"}: ${Math.round(value)} out of 100`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--line)" strokeWidth="6" />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={tone} strokeWidth="6" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - Math.min(value, 100) / 100)} transform={`rotate(-90 ${size / 2} ${size / 2})`} />
      </svg>
      <span style={{ fontSize: size / 3.4 }}>{Math.round(value)}</span>
    </div>
  );
}

export function Bar({ value, tone = "brand" }: { value: number; tone?: "brand" | "warn" | "bad" | "good" }) {
  return (
    <div className="bar" aria-hidden="true">
      <div className={`bar-fill bar-${tone}`} style={{ width: `${Math.max(2, Math.min(100, value))}%` }} />
    </div>
  );
}

export function Loading({ text = "Loading…" }: { text?: string }) {
  return <p className="muted" role="status"><span className="spinner" aria-hidden="true" /> {text}</p>;
}

export function ErrorBox({ error }: { error: ApiError | string | null }) {
  if (!error) return null;
  const message = typeof error === "string" ? error : error.message;
  return <div className="alert alert-bad" role="alert">{message}</div>;
}

export function NeedCv({ error }: { error: ApiError | null }) {
  if (error?.code === "NO_PROFILE") {
    return (
      <Card>
        <p><strong>Upload your CV first.</strong> The Profile Understanding Agent needs it before the other agents can help.</p>
        <Link className="btn" href="/dashboard/profile">Go to Profile and CV</Link>
      </Card>
    );
  }
  return <ErrorBox error={error} />;
}

export const money = (n: number) => `$${Math.round(n / 1000)}k`;

/** Human label for an agent run's llm_source (see backend/app/tracking.py). */
export const sourceLabel = (src?: string) =>
  ({ rules: "Rules (calculation)", llm: "LLM", template: "Template (no LLM set)", "template-fallback": "Template (LLM failed)", adzuna: "Adzuna API (live)", "adzuna+sample": "Adzuna + sample jobs", "sample-data": "Sample jobs (fallback)" } as Record<string, string>)[src ?? ""] ?? (src || "-");
