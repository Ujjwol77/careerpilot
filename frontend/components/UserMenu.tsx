"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";
import { token } from "@/lib/api";
import { ThemeToggle } from "@/components/ThemeToggle";

/** Sidebar account button: click the name to open theme, home page and log out options. */
export function UserMenu({ name, email }: { name: string; email: string }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const wrap = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const panelId = useId();

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => { if (!wrap.current?.contains(e.target as Node)) setOpen(false); };
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") { setOpen(false); trigger.current?.focus(); } };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    wrap.current?.querySelector<HTMLElement>(".usermenu-panel button, .usermenu-panel a")?.focus();
    return () => { document.removeEventListener("mousedown", onDown); document.removeEventListener("keydown", onKey); };
  }, [open]);

  function logOut() {
    token.clear();
    router.replace("/login");
  }

  return (
    <div className="usermenu" ref={wrap}>
      {open && (
        <div className="usermenu-panel" id={panelId} role="dialog" aria-label="Account and settings">
          <div className="usermenu-who">
            <strong>{name}</strong>
            <span>{email}</span>
          </div>
          <div className="usermenu-section">
            <span className="usermenu-label" id={`${panelId}-theme`}>Theme</span>
            <ThemeToggle />
          </div>
          <Link className="usermenu-item" href="/" onClick={() => setOpen(false)}>Go to home page</Link>
          <button type="button" className="usermenu-item usermenu-logout" onClick={logOut}>Log out</button>
        </div>
      )}
      <button ref={trigger} type="button" className="usermenu-trigger" aria-haspopup="dialog" aria-expanded={open}
        aria-controls={open ? panelId : undefined} onClick={() => setOpen((o) => !o)}>
        <span className="usermenu-avatar" aria-hidden="true">{(name || email || "?").trim().charAt(0).toUpperCase()}</span>
        <span className="usermenu-text">
          <span className="usermenu-name">{name}</span>
          <span className="usermenu-email">{email}</span>
        </span>
        <span className="usermenu-caret" aria-hidden="true">{open ? "▾" : "▴"}</span>
      </button>
    </div>
  );
}
