"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, token } from "@/lib/api";

const NAV = [
  { href: "/dashboard", label: "Overview" },
  { group: "Profile" },
  { href: "/dashboard/profile", label: "Profile and CV" },
  { href: "/dashboard/cv", label: "CV review" },
  { group: "Opportunities" },
  { href: "/dashboard/jobs", label: "Jobs and matching" },
  { href: "/dashboard/applications", label: "Applications" },
  { group: "Growth" },
  { href: "/dashboard/skills", label: "Skill gaps" },
  { href: "/dashboard/learning", label: "Learning path" },
  { href: "/dashboard/interview", label: "Interview practice" },
  { group: "Outputs" },
  { href: "/dashboard/report", label: "Readiness report" },
  { href: "/dashboard/ops", label: "Agent monitor" },
] as const;

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const path = usePathname();
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);

  useEffect(() => {
    if (!token.get()) { router.replace("/login"); return; }
    api("/auth/me").then(setUser).catch(() => router.replace("/login"));
  }, [router]);

  if (!user) return <p className="muted" style={{ padding: 24 }}>Loading…</p>;

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand"><img src="/logo.svg" alt="" width={28} height={28} /> CareerPilot</div>
        <nav className="nav" aria-label="Main">
          {NAV.map((item, i) =>
            "group" in item ? (
              <div key={i} className="group">{item.group}</div>
            ) : (
              <Link key={item.href} href={item.href} aria-current={path === item.href ? "page" : undefined}>{item.label}</Link>
            )
          )}
        </nav>
        <div className="userbox">
          <div style={{ color: "#fff", fontWeight: 600 }}>{user.name || "Job seeker"}</div>
          <div>{user.email}</div>
          <button className="btn btn-ghost btn-small" style={{ marginTop: 10, color: "inherit", borderColor: "rgba(255,255,255,.25)" }}
            onClick={() => { token.clear(); router.replace("/login"); }}>Log out</button>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
