"use client";
import { useEffect, useId, useRef, useState, type ReactNode } from "react";

/**
 * Small circular "i" button that reveals an explanation.
 * Mouse: shows on hover. Keyboard: shows on focus. Touch or click: toggles open, so it stays readable.
 * Escape or a click elsewhere closes it. The text is linked to the button for screen readers.
 */
export function InfoTip({ children, label = "More information" }: { children: ReactNode; label?: string }) {
  const id = useId();
  const [pinned, setPinned] = useState(false);
  const [dismissed, setDismissed] = useState(false); // Escape hides it even while hovered or focused
  const [alignRight, setAlignRight] = useState(false);
  const wrap = useRef<HTMLSpanElement>(null);

  // keep the bubble on screen: near the right edge it opens leftwards
  function place() {
    const r = wrap.current?.getBoundingClientRect();
    if (r) setAlignRight(r.left > window.innerWidth - 300);
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
    <span ref={wrap} className={`infotip${pinned ? " open" : ""}${alignRight ? " right" : ""}${dismissed ? " dismissed" : ""}`}
      onMouseEnter={place} onMouseLeave={() => setDismissed(false)}
      onKeyDown={(e) => { if (e.key === "Escape") { setPinned(false); setDismissed(true); } }}>
      <button type="button" className="infotip-btn" aria-label={label} aria-describedby={id} aria-expanded={pinned}
        onFocus={place} onBlur={() => setDismissed(false)} onClick={() => { place(); setDismissed(false); setPinned((p) => !p); }}>
        <span aria-hidden="true">i</span>
      </button>
      <span role="tooltip" id={id} className="infotip-bubble">{children}</span>
    </span>
  );
}
