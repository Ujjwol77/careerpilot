"use client";
import { useEffect, useId, useRef, useState, type ReactNode } from "react";

/**
 * Small circular "i" button that reveals an explanation.
 * Mouse: shows on hover. Keyboard: shows on focus. Touch or click: toggles open, so it stays readable.
 * Escape or a click elsewhere closes it. The bubble is shifted sideways so it always fits on screen. The text is linked to the button for screen readers.
 */
export function InfoTip({ children, label = "More information" }: { children: ReactNode; label?: string }) {
  const id = useId();
  const [pinned, setPinned] = useState(false);
  const [dismissed, setDismissed] = useState(false); // Escape hides it even while hovered or focused
  const [shift, setShift] = useState(-8); // bubble's left edge, relative to the icon
  const wrap = useRef<HTMLSpanElement>(null);
  const bubble = useRef<HTMLSpanElement>(null);

  // keep the whole bubble on screen, with an 8px margin, on any screen width
  function place() {
    const r = wrap.current?.getBoundingClientRect();
    const w = bubble.current?.offsetWidth ?? 280;
    if (!r) return;
    const vw = document.documentElement.clientWidth;
    let left = -8;
    if (r.left + left + w > vw - 8) left = vw - 8 - w - r.left;
    if (r.left + left < 8) left = 8 - r.left;
    setShift(Math.round(left));
  }

  useEffect(() => {
    if (!pinned) return;
    const onDown = (e: MouseEvent | TouchEvent) => { if (!wrap.current?.contains(e.target as Node)) setPinned(false); };
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") { setPinned(false); setDismissed(true); } };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("touchstart", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("touchstart", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [pinned]);

  return (
    <span ref={wrap} className={`infotip${pinned ? " open" : ""}${dismissed ? " dismissed" : ""}`}
      onMouseEnter={place} onMouseLeave={() => setDismissed(false)}
      onKeyDown={(e) => { if (e.key === "Escape") { setPinned(false); setDismissed(true); } }}>
      <button type="button" className="infotip-btn" aria-label={label} aria-describedby={id} aria-expanded={pinned}
        onFocus={place} onBlur={() => setDismissed(false)} onClick={() => { place(); setDismissed(false); setPinned((p) => !p); }}>
        <span aria-hidden="true">i</span>
      </button>
      <span ref={bubble} role="tooltip" id={id} className="infotip-bubble" style={{ left: shift }}>{children}</span>
    </span>
  );
}
