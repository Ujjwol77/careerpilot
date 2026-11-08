"use client";
import { useEffect, useRef, useState, type ReactNode } from "react";

/* ---------- tooltip ---------- */
type Tip = { x: number; y: number; content: ReactNode } | null;

export function useTip() {
  const ref = useRef<HTMLDivElement>(null);
  const [tip, setTip] = useState<Tip>(null);
  const show = (e: React.MouseEvent | React.FocusEvent, content: ReactNode) => {
    const box = ref.current?.getBoundingClientRect();
    if (!box) return;
    if ("clientX" in e) {
      setTip({ x: e.clientX - box.left, y: e.clientY - box.top, content });
    } else {
      const r = (e.currentTarget as Element).getBoundingClientRect();
      setTip({ x: r.left - box.left + r.width / 2, y: r.top - box.top, content });
    }
  };
  const hide = () => setTip(null);
  const node = tip ? (
    <div className="tip" style={{ left: tip.x, top: tip.y }} role="tooltip">{tip.content}</div>
  ) : null;
  return { ref, show, hide, node };
}

/* ---------- count-up number ---------- */
export function CountUp({ value, decimals = 0, suffix = "" }: { value: number; decimals?: number; suffix?: string }) {
  const [v, setV] = useState(0);
  useEffect(() => {
    if (typeof window === "undefined" || window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setV(value); return; }
    let raf = 0;
    const t0 = performance.now();
    const tick = (t: number) => {
      const p = Math.min(1, (t - t0) / 900);
      setV(value * (1 - Math.pow(1 - p, 3)));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value]);
  return <>{v.toFixed(decimals)}{suffix}</>;
}

/* ---------- KPI tile ---------- */
export function Kpi({ label, value, decimals = 0, suffix = "", hint, accent = "var(--s1)" }: {
  label: string; value: number | null; decimals?: number; suffix?: string; hint?: string; accent?: string;
}) {
  return (
    <div className="kpi lift" style={{ ["--accent" as string]: accent }}>
      <div className="kpi-value">{value === null ? "–" : <CountUp value={value} decimals={decimals} suffix={suffix} />}</div>
      <div className="kpi-label">{label}</div>
      {hint && <div className="kpi-hint">{hint}</div>}
    </div>
  );
}

/* ---------- legend ---------- */
export function Legend({ items }: { items: { label: string; color: string }[] }) {
  return (
    <ul className="legend">
      {items.map((i, idx) => (
        <li key={`${i.label}-${idx}`}><span className="swatch" style={{ background: i.color }} aria-hidden="true" />{i.label}</li>
      ))}
    </ul>
  );
}

/* ---------- horizontal bars ---------- */
export type BarRow = { label: string; value: number; display?: string; color?: string; tip?: ReactNode };

export function HBarChart({ rows, max = 100, ariaLabel }: { rows: BarRow[]; max?: number; ariaLabel: string }) {
  const { ref, show, hide, node } = useTip();
  const [active, setActive] = useState<number | null>(null);
  const tipFor = (r: BarRow) => r.tip ?? <><strong>{r.label}</strong><br />{r.display ?? Math.round(r.value)}</>;
  return (
    <div className="chart" ref={ref} role="list" aria-label={ariaLabel} onMouseLeave={() => { hide(); setActive(null); }}>
      {rows.map((r, i) => (
        <div
          key={`${r.label}-${i}`}
          role="listitem"
          tabIndex={0}
          className={`hbar ${active !== null && active !== i ? "dim" : ""}`}
          onMouseMove={(e) => { setActive(i); show(e, tipFor(r)); }}
          onFocus={(e) => { setActive(i); show(e, tipFor(r)); }}
          onBlur={() => { hide(); setActive(null); }}
        >
          <span className="hbar-label" title={r.label}>{r.label}</span>
          <span className="hbar-track">
            <span className="hbar-fill" style={{ width: `${Math.max(1, Math.min(100, (r.value / max) * 100))}%`, background: r.color ?? "var(--s1)", animationDelay: `${i * 70}ms` }} />
          </span>
          <span className="hbar-value">{r.display ?? Math.round(r.value)}</span>
        </div>
      ))}
      {node}
    </div>
  );
}

/* ---------- stacked bar (score composition) ---------- */
export type Part = { label: string; value: number; color: string; note?: string };

export function StackBar({ parts, total = 100, ariaLabel }: { parts: Part[]; total?: number; ariaLabel: string }) {
  const { ref, show, hide, node } = useTip();
  const [active, setActive] = useState<number | null>(null);
  return (
    <div className="chart stack-wrap" ref={ref} onMouseLeave={() => { hide(); setActive(null); }}>
      <div className="stackbar" role="img" aria-label={ariaLabel}>
        {parts.map((p, i) => (
          <span
            key={`${p.label}-${i}`}
            className={`stackseg ${active !== null && active !== i ? "dim" : ""}`}
            style={{ width: `${(p.value / total) * 100}%`, background: p.color, animationDelay: `${i * 90}ms` }}
            onMouseMove={(e) => { setActive(i); show(e, <><strong>{p.label}</strong><br />{p.value.toFixed(1)} points{p.note ? <><br /><span className="tip-sub">{p.note}</span></> : null}</>); }}
          />
        ))}
      </div>
      {node}
    </div>
  );
}

/* ---------- donut ---------- */
export type Slice = { label: string; value: number; color: string };

export function Donut({ slices, centerValue, centerLabel, ariaLabel }: {
  slices: Slice[]; centerValue?: string; centerLabel?: string; ariaLabel: string;
}) {
  const { ref, show, hide, node } = useTip();
  const [active, setActive] = useState<number | null>(null);
  const total = slices.reduce((s, x) => s + x.value, 0);
  const R = 52;
  const C = 2 * Math.PI * R;
  let offset = 0;
  const pct = (v: number) => (total ? Math.round((v / total) * 100) : 0);
  return (
    <div className="donut-wrap">
      <div className="chart donut" ref={ref} onMouseLeave={() => { hide(); setActive(null); }}>
        <svg viewBox="0 0 140 140" role="img" aria-label={ariaLabel}>
          <circle cx="70" cy="70" r={R} fill="none" stroke="var(--line)" strokeWidth="16" />
          {slices.map((s, i) => {
            const len = total ? (s.value / total) * C : 0;
            const dash = Math.max(0, len - 2);
            const el = (
              <circle
                key={`${s.label}-${i}`}
                className="donut-seg"
                cx="70" cy="70" r={R} fill="none" stroke={s.color}
                strokeWidth={active === i ? 21 : 16}
                strokeDasharray={`${dash} ${C - dash}`}
                strokeDashoffset={-offset}
                transform="rotate(-90 70 70)"
                opacity={active !== null && active !== i ? 0.35 : 1}
                onMouseMove={(e) => { setActive(i); show(e, <><strong>{s.label}</strong><br />{s.value} ({pct(s.value)}%)</>); }}
              />
            );
            offset += len;
            return el;
          })}
          <text x="70" y="68" textAnchor="middle" className="donut-num">{centerValue ?? total}</text>
          <text x="70" y="86" textAnchor="middle" className="donut-cap">{centerLabel ?? "total"}</text>
        </svg>
        {node}
      </div>
      <ul className="legend legend-col">
        {slices.map((s, i) => (
          <li key={`${s.label}-${i}`} className={active !== null && active !== i ? "dim" : ""} onMouseEnter={() => setActive(i)} onMouseLeave={() => setActive(null)}>
            <span className="swatch" style={{ background: s.color }} aria-hidden="true" />
            <span>{s.label}</span><strong>{s.value}</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ---------- radar ---------- */
export type Axis = { label: string; value: number; tip?: ReactNode };

export function Radar({ axes, ariaLabel }: { axes: Axis[]; ariaLabel: string }) {
  const { ref, show, hide, node } = useTip();
  const [active, setActive] = useState<number | null>(null);
  const N = axes.length;
  const cx = 170, cy = 140, R = 88;
  const pt = (i: number, r: number): [number, number] => {
    const a = -Math.PI / 2 + (2 * Math.PI * i) / N;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  };
  const poly = (r: number) => axes.map((_, i) => pt(i, r).join(",")).join(" ");
  const data = axes.map((a, i) => pt(i, (Math.max(0, Math.min(100, a.value)) / 100) * R).join(",")).join(" ");
  return (
    <div className="chart" ref={ref} onMouseLeave={() => { hide(); setActive(null); }}>
      <svg viewBox="0 0 340 280" role="img" aria-label={ariaLabel} className="radar">
        {[25, 50, 75, 100].map((p) => (
          <polygon key={p} points={poly((p / 100) * R)} fill="none" stroke="var(--line)" strokeWidth="1" />
        ))}
        {axes.map((_, i) => {
          const [x, y] = pt(i, R);
          return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="var(--line)" strokeWidth="1" />;
        })}
        <polygon className="radar-area" points={data} fill="var(--s1)" fillOpacity="0.2" stroke="var(--s1)" strokeWidth="2" strokeLinejoin="round" />
        {axes.map((a, i) => {
          const [x, y] = pt(i, (Math.max(0, Math.min(100, a.value)) / 100) * R);
          const [lx, ly] = pt(i, R + 20);
          const anchor = Math.abs(lx - cx) < 8 ? "middle" : lx > cx ? "start" : "end";
          const tipNode = a.tip ?? <><strong>{a.label}</strong><br />{Math.round(a.value)}%</>;
          return (
            <g key={`${a.label}-${i}`}>
              <text x={lx} y={ly + 4} textAnchor={anchor} className="radar-label">{a.label}</text>
              <text x={lx} y={ly + 18} textAnchor={anchor} className="radar-val">{Math.round(a.value)}%</text>
              <circle cx={x} cy={y} r={active === i ? 7 : 5} fill="var(--s1)" stroke="var(--card)" strokeWidth="2" style={{ transition: "r .15s" }} />
              <circle cx={x} cy={y} r="16" fill="transparent" tabIndex={0}
                onMouseMove={(e) => { setActive(i); show(e, tipNode); }}
                onFocus={(e) => { setActive(i); show(e, tipNode); }}
                onBlur={() => { hide(); setActive(null); }} />
            </g>
          );
        })}
      </svg>
      {node}
    </div>
  );
}

/* ---------- line chart ---------- */
export type LinePoint = { label: string; value: number };

export function LineChart({ points, max = 10, ariaLabel, unit = "" }: { points: LinePoint[]; max?: number; ariaLabel: string; unit?: string }) {
  const { ref, show, hide, node } = useTip();
  const [hover, setHover] = useState<number | null>(null);
  const W = 520, H = 200, L = 34, Rr = 16, T = 14, B = 30;
  const n = points.length;
  const x = (i: number) => (n === 1 ? (L + W - Rr) / 2 : L + (i * (W - L - Rr)) / (n - 1));
  const y = (v: number) => T + (1 - v / max) * (H - T - B);
  const path = points.map((p, i) => `${i ? "L" : "M"}${x(i)} ${y(p.value)}`).join("");
  const area = n > 1 ? `${path}L${x(n - 1)} ${H - B}L${x(0)} ${H - B}Z` : "";
  const move = (e: React.MouseEvent<SVGRectElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const sx = ((e.clientX - r.left) / r.width) * W;
    const i = n === 1 ? 0 : Math.max(0, Math.min(n - 1, Math.round(((sx - L) / (W - L - Rr)) * (n - 1))));
    setHover(i);
    show(e, <><strong>{points[i].label}</strong><br />{points[i].value}{unit}</>);
  };
  return (
    <div className="chart" ref={ref} onMouseLeave={() => { hide(); setHover(null); }}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={ariaLabel} className="line">
        {[0, max / 2, max].map((g) => (
          <g key={g}>
            <line x1={L} x2={W - Rr} y1={y(g)} y2={y(g)} stroke="var(--line)" strokeWidth="1" />
            <text x={L - 8} y={y(g) + 4} textAnchor="end" className="axis">{g}</text>
          </g>
        ))}
        {area && <path d={area} fill="var(--s1)" fillOpacity="0.12" />}
        {n > 1 && <path className="line-path" d={path} pathLength={1} fill="none" stroke="var(--s1)" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />}
        {hover !== null && <line x1={x(hover)} x2={x(hover)} y1={T} y2={H - B} stroke="var(--muted)" strokeWidth="1" strokeDasharray="3 3" />}
        {points.map((p, i) => (
          <g key={i}>
            <circle cx={x(i)} cy={y(p.value)} r={hover === i ? 6 : 4} fill="var(--s1)" stroke="var(--card)" strokeWidth="2" style={{ transition: "r .15s" }} />
            {(n <= 8 || i === 0 || i === n - 1) && <text x={x(i)} y={H - 10} textAnchor="middle" className="axis">{p.label}</text>}
          </g>
        ))}
        <rect x={L} y={T} width={W - L - Rr} height={H - T - B} fill="transparent" onMouseMove={move} />
      </svg>
      {node}
    </div>
  );
}
