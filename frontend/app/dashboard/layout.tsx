"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
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
  const [navOpen, setNavOpen] = useState(false); // mobile drawer
  const hamburger = useRef<HTMLButtonElement>(null);
  const drawer = useRef<HTMLElement>(null);

  // close the mobile drawer whenever the page changes
  useEffect(() => { setNavOpen(false); }, [path]);
  // while the drawer is open: Escape closes it, focus moves into it, and the page behind doesn't scroll
  useEffect(() => {
    if (!navOpen) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") { setNavOpen(false); hamburger.current?.focus(); } };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    drawer.current?.querySelector<HTMLElement>(".nav a")?.focus();
    return () => { document.removeEventListener("keydown", onKey); document.body.style.overflow = ""; };
  }, [navOpen]);

  // remember the sidebar state between visits (storage can be unavailable, so never rely on it)
  useEffect(() => {
    try { setCollapsed(window.localStorage.getItem("cp_sidebar") === "collapsed"); } catch { /* ignore */ }
  }, []);
  function onBrandClick() {
    // phones and narrow windows: the logo closes the drawer; wider screens: it collapses the sidebar
    if (window.matchMedia("(max-width: 860px)").matches) { setNavOpen(false); hamburger.current?.focus(); return; }
    toggleSidebar();
  }
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
    <div className={`shell${collapsed ? " collapsed" : ""}${navOpen ? " nav-open" : ""}`}>
      <button ref={hamburger} type="button" className="hamburger" aria-label={navOpen ? "Close menu" : "Open menu"}
        aria-expanded={navOpen} aria-controls="sidebar" onClick={() => setNavOpen((o) => !o)}>
        <span aria-hidden="true" /><span aria-hidden="true" /><span aria-hidden="true" />
      </button>
      {navOpen && <div className="nav-backdrop" onClick={() => setNavOpen(false)} aria-hidden="true" />}
      <aside className="sidebar" id="sidebar" ref={drawer}>
        <button type="button" className="brand brand-btn" onClick={onBrandClick} aria-expanded={!collapsed} aria-controls="main-nav"
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
