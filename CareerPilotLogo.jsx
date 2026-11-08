// CareerPilot logo — drop into src/components/
// Usage: <CareerPilotLogo size={40} /> or <CareerPilotLogo size={40} variant="dark" showText={false} />
export default function CareerPilotLogo({ size = 40, variant = "light", showText = true }) {
  const navy = "#12305B";
  const text = variant === "dark" ? "#FFFFFF" : navy;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: size * 0.3 }}>
      <svg width={size} height={size} viewBox="0 0 120 120" role="img" aria-label="CareerPilot">
        <rect width="120" height="120" rx="28" fill={variant === "dark" ? "#FFFFFF" : navy} />
        <path d="M24 96 C 38 94, 46 80, 56 66" fill="none" stroke="#F2A33A" strokeWidth="5" strokeLinecap="round" strokeDasharray="2 9" />
        <polygon points="96,24 46,46 64,55" fill={variant === "dark" ? navy : "#FFFFFF"} />
        <polygon points="96,24 64,55 73,76" fill={variant === "dark" ? "#3D5F94" : "#BFD0EA"} />
        <polygon points="64,55 60,68 73,76" fill={variant === "dark" ? "#6C88B8" : "#8FA9D3"} />
      </svg>
      {showText && (
        <span style={{ fontFamily: "'Space Grotesk', Inter, sans-serif", fontSize: size * 0.6, letterSpacing: "-0.02em", color: text, lineHeight: 1 }}>
          <span style={{ fontWeight: 500 }}>Career</span><span style={{ fontWeight: 700 }}>Pilot</span>
        </span>
      )}
    </div>
  );
}
