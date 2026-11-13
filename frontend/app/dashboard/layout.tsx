"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, token } from "@/lib/api";
import { UserMenu } from "@/components/UserMenu";

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
  const [collapsed, setCollapsed] = useState(false);

  // remember the sidebar state between visits (storage can be unavailable, so never rely on it)
  useEffect(() => {
    try { setCollapsed(window.localStorage.getItem("cp_sidebar") === "collapsed"); } catch { /* ignore */ }
  }, []);
  function toggleSidebar() {
    setCollapsed((c) => {
      try { window.localStorage.setItem("cp_sidebar", c ? "open" : "collapsed"); } catch { /* ignore */ }
      return !c;
    });
  }

  useEffect(() => {
    if (!token.get()) { router.replace("/login"); return; }
    api("/auth/me").then(setUser).catch(() => router.replace("/login"));
  }, [router]);

  if (!user) return <p className="muted" style={{ padding: 24 }}>Loading…</p>;

  return (
    <div className={collapsed ? "shell collapsed" : "shell"}>
      <aside className="sidebar">
        <button type="button" className="brand brand-btn" onClick={toggleSidebar} aria-expanded={!collapsed} aria-controls="main-nav"
          title={collapsed ? "Show menu" : "Hide menu"} aria-label={collapsed ? "Show menu" : "Hide menu"}>
          <img src="/logo.svg" alt="" width={28} height={28} /> <span className="brand-name">CareerPilot</span>
        </button>
        <nav className="nav" id="main-nav" aria-label="Main">
          {NAV.map((item, i) =>
            "group" in item ? (
              <div key={i} className="group">{item.group}</div>
            ) : (
              <Link key={item.href} href={item.href} aria-current={path === item.href ? "page" : undefined}>{item.label}</Link>
            )
          )}
        </nav>
        <div className="userbox">
          <UserMenu name={user.name || "Job seeker"} email={user.email} />
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
