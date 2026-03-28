import { useState } from "react";

const sampleData = {
  distance: "5.23",
  unit: "KM",
  pace: "5'42\"",
  time: "29:48",
  calories: "312",
  elevation: "+42m",
  heartRate: "156",
  date: "28 MAR 2026",
  location: "Eco Horizon, Penang",
};

// ─────────────────────────────────────────────
// CONCEPT A — "Glass Slab" (frosted glass + map peek-through)
// ─────────────────────────────────────────────
function ConceptA() {
  return (
    <div
      style={{
        width: 340,
        position: "relative",
        borderRadius: 24,
        overflow: "hidden",
        background: "linear-gradient(145deg, #1a3a2a 0%, #0d1f15 100%)",
        fontFamily: "'DM Sans', sans-serif",
      }}
    >
      {/* Simulated map background */}
      <div
        style={{
          height: 280,
          background:
            "linear-gradient(180deg, rgba(34,85,60,0.4) 0%, rgba(13,31,21,0.9) 100%), repeating-linear-gradient(0deg, transparent, transparent 20px, rgba(255,255,255,0.03) 20px, rgba(255,255,255,0.03) 21px), repeating-linear-gradient(90deg, transparent, transparent 20px, rgba(255,255,255,0.03) 20px, rgba(255,255,255,0.03) 21px)",
          position: "relative",
        }}
      >
        {/* Route polyline simulation */}
        <svg
          viewBox="0 0 340 280"
          style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
        >
          <path
            d="M60,240 Q80,200 120,180 T200,120 Q240,90 260,100 T300,60"
            fill="none"
            stroke="#4ade80"
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray="8,4"
            opacity="0.7"
          />
          <circle cx="60" cy="240" r="5" fill="#4ade80" />
          <circle cx="300" cy="60" r="5" fill="#f97316" />
        </svg>
        {/* Date + location pill */}
        <div
          style={{
            position: "absolute",
            top: 16,
            left: 16,
            display: "flex",
            alignItems: "center",
            gap: 6,
            background: "rgba(0,0,0,0.35)",
            backdropFilter: "blur(12px)",
            WebkitBackdropFilter: "blur(12px)",
            borderRadius: 20,
            padding: "6px 14px",
            color: "rgba(255,255,255,0.75)",
            fontSize: 11,
            fontWeight: 500,
            letterSpacing: "0.03em",
          }}
        >
          <span style={{ color: "#4ade80" }}>●</span>
          {sampleData.date} · {sampleData.location}
        </div>
      </div>

      {/* Glass stats card */}
      <div
        style={{
          margin: "-40px 16px 16px 16px",
          position: "relative",
          zIndex: 2,
          background: "rgba(255,255,255,0.08)",
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)",
          borderRadius: 20,
          border: "1px solid rgba(255,255,255,0.12)",
          padding: "20px 20px 16px",
        }}
      >
        {/* Hero stat */}
        <div style={{ textAlign: "center", marginBottom: 16 }}>
          <div
            style={{
              fontSize: 52,
              fontWeight: 700,
              color: "#fff",
              lineHeight: 1,
              letterSpacing: "-0.03em",
            }}
          >
            {sampleData.distance}
            <span
              style={{
                fontSize: 18,
                fontWeight: 500,
                color: "rgba(255,255,255,0.5)",
                marginLeft: 4,
              }}
            >
              {sampleData.unit}
            </span>
          </div>
        </div>

        {/* Divider */}
        <div
          style={{
            height: 1,
            background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent)",
            marginBottom: 14,
          }}
        />

        {/* Stats row */}
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          {[
            { label: "PACE", value: sampleData.pace },
            { label: "TIME", value: sampleData.time },
            { label: "CAL", value: sampleData.calories },
            { label: "ELEV", value: sampleData.elevation },
          ].map((s, i) => (
            <div key={i} style={{ textAlign: "center", flex: 1 }}>
              <div
                style={{
                  fontSize: 10,
                  fontWeight: 600,
                  color: "rgba(255,255,255,0.35)",
                  letterSpacing: "0.1em",
                  marginBottom: 4,
                }}
              >
                {s.label}
              </div>
              <div
                style={{
                  fontSize: 16,
                  fontWeight: 600,
                  color: "#fff",
                }}
              >
                {s.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// CONCEPT B — "Clipboard Card" (matches your sketch — stacked rows)
// ─────────────────────────────────────────────
function ConceptB() {
  const rows = [
    { icon: "↗", label: "Distance", value: sampleData.distance + " km", accent: "#ff6b35" },
    { icon: "⏱", label: "Duration", value: sampleData.time, accent: "#ff6b35" },
    { icon: "◎", label: "Avg Pace", value: sampleData.pace + " /km", accent: "#ff6b35" },
    { icon: "♥", label: "Heart Rate", value: sampleData.heartRate + " bpm", accent: "#ff4444" },
    { icon: "▲", label: "Elevation", value: sampleData.elevation, accent: "#ff6b35" },
  ];

  return (
    <div
      style={{
        width: 320,
        fontFamily: "'DM Mono', 'Courier New', monospace",
        position: "relative",
      }}
    >
      {/* Tab / clip at top */}
      <div
        style={{
          width: 70,
          height: 24,
          background: "#ff6b35",
          borderRadius: "8px 8px 0 0",
          marginLeft: 40,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span style={{ fontSize: 9, fontWeight: 700, color: "#fff", letterSpacing: "0.12em" }}>
          RUN
        </span>
      </div>

      {/* Main card */}
      <div
        style={{
          background: "#fff",
          borderRadius: "0 12px 12px 12px",
          border: "2.5px solid #ff6b35",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            background: "#ff6b35",
            padding: "12px 18px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span style={{ color: "#fff", fontSize: 11, fontWeight: 700, letterSpacing: "0.08em" }}>
            {sampleData.date}
          </span>
          <span
            style={{
              color: "rgba(255,255,255,0.7)",
              fontSize: 10,
              fontWeight: 500,
            }}
          >
            {sampleData.location}
          </span>
        </div>

        {/* Hero number */}
        <div
          style={{
            padding: "20px 18px 12px",
            borderBottom: "1.5px dashed rgba(255,107,53,0.2)",
          }}
        >
          <div style={{ fontSize: 10, color: "#999", fontWeight: 600, letterSpacing: "0.1em" }}>
            TOTAL DISTANCE
          </div>
          <div
            style={{
              fontSize: 44,
              fontWeight: 700,
              color: "#1a1a1a",
              lineHeight: 1.1,
              letterSpacing: "-0.02em",
              fontFamily: "'DM Sans', sans-serif",
            }}
          >
            {sampleData.distance}
            <span style={{ fontSize: 16, color: "#999", marginLeft: 4 }}>km</span>
          </div>
        </div>

        {/* Stat rows */}
        {rows.map((row, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "10px 18px",
              borderBottom:
                i < rows.length - 1 ? "1px solid rgba(0,0,0,0.06)" : "none",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span
                style={{
                  width: 26,
                  height: 26,
                  borderRadius: 6,
                  background: `${row.accent}12`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 13,
                }}
              >
                {row.icon}
              </span>
              <span style={{ fontSize: 12, color: "#888", fontWeight: 500 }}>{row.label}</span>
            </div>
            <span
              style={{
                fontSize: 15,
                fontWeight: 700,
                color: "#1a1a1a",
                fontFamily: "'DM Sans', sans-serif",
              }}
            >
              {row.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// CONCEPT C — "Neon Split" (bold split-screen with gradient accent)
// ─────────────────────────────────────────────
function ConceptC() {
  return (
    <div
      style={{
        width: 340,
        borderRadius: 20,
        overflow: "hidden",
        background: "#0a0a0a",
        fontFamily: "'DM Sans', sans-serif",
        position: "relative",
      }}
    >
      {/* Gradient glow accent */}
      <div
        style={{
          position: "absolute",
          top: -40,
          right: -40,
          width: 180,
          height: 180,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(255,107,53,0.3) 0%, transparent 70%)",
          filter: "blur(30px)",
        }}
      />

      {/* Top section — big stat */}
      <div style={{ padding: "28px 24px 0", position: "relative" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: 8,
          }}
        >
          <div>
            <div
              style={{
                fontSize: 10,
                fontWeight: 700,
                color: "rgba(255,255,255,0.3)",
                letterSpacing: "0.15em",
                marginBottom: 8,
              }}
            >
              MORNING RUN
            </div>
            <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
              <span
                style={{
                  fontSize: 64,
                  fontWeight: 800,
                  color: "#fff",
                  lineHeight: 1,
                  letterSpacing: "-0.04em",
                }}
              >
                {sampleData.distance}
              </span>
              <span
                style={{
                  fontSize: 20,
                  fontWeight: 600,
                  color: "rgba(255,255,255,0.3)",
                }}
              >
                km
              </span>
            </div>
          </div>

          {/* Mini route */}
          <svg width="80" height="70" viewBox="0 0 80 70">
            <path
              d="M10,60 Q20,40 35,35 T55,20 Q65,12 75,15"
              fill="none"
              stroke="url(#grad)"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
            <defs>
              <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#ff6b35" />
                <stop offset="100%" stopColor="#ff3366" />
              </linearGradient>
            </defs>
            <circle cx="10" cy="60" r="3" fill="#ff6b35" />
            <circle cx="75" cy="15" r="3" fill="#ff3366" />
          </svg>
        </div>

        {/* Pace highlight bar */}
        <div
          style={{
            background: "linear-gradient(90deg, #ff6b35, #ff3366)",
            borderRadius: 12,
            padding: "14px 18px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: 12,
          }}
        >
          <div>
            <div
              style={{
                fontSize: 9,
                fontWeight: 700,
                color: "rgba(255,255,255,0.6)",
                letterSpacing: "0.12em",
              }}
            >
              AVG PACE
            </div>
            <div style={{ fontSize: 26, fontWeight: 800, color: "#fff", lineHeight: 1.1 }}>
              {sampleData.pace}
              <span style={{ fontSize: 12, fontWeight: 500, opacity: 0.6 }}> /km</span>
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div
              style={{
                fontSize: 9,
                fontWeight: 700,
                color: "rgba(255,255,255,0.6)",
                letterSpacing: "0.12em",
              }}
            >
              DURATION
            </div>
            <div style={{ fontSize: 26, fontWeight: 800, color: "#fff", lineHeight: 1.1 }}>
              {sampleData.time}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom stats grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: 0,
          padding: "16px 24px 20px",
        }}
      >
        {[
          { label: "CALORIES", value: sampleData.calories, suffix: " kcal" },
          { label: "HEART RATE", value: sampleData.heartRate, suffix: " bpm" },
          { label: "ELEVATION", value: sampleData.elevation, suffix: "" },
        ].map((s, i) => (
          <div
            key={i}
            style={{
              textAlign: "center",
              padding: "8px 0",
              borderLeft: i > 0 ? "1px solid rgba(255,255,255,0.06)" : "none",
            }}
          >
            <div
              style={{
                fontSize: 9,
                fontWeight: 700,
                color: "rgba(255,255,255,0.25)",
                letterSpacing: "0.1em",
                marginBottom: 6,
              }}
            >
              {s.label}
            </div>
            <div style={{ fontSize: 16, fontWeight: 700, color: "#fff" }}>
              {s.value}
              <span style={{ fontSize: 10, color: "rgba(255,255,255,0.35)" }}>{s.suffix}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Footer line */}
      <div
        style={{
          padding: "0 24px 14px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span
          style={{
            fontSize: 10,
            color: "rgba(255,255,255,0.2)",
            fontWeight: 500,
          }}
        >
          {sampleData.date}
        </span>
        <span
          style={{
            fontSize: 10,
            color: "rgba(255,255,255,0.2)",
            fontWeight: 500,
          }}
        >
          {sampleData.location}
        </span>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Main App — Tab switcher
// ─────────────────────────────────────────────
const concepts = [
  {
    id: "A",
    name: "Glass Slab",
    desc: "Frosted glass card overlaid on the map. Hero distance stat + compact row. Minimal, Instagram-story-ready.",
    Component: ConceptA,
  },
  {
    id: "B",
    name: "Clipboard Card",
    desc: "Matches your sketch — tabbed card with stacked stat rows. Clean data hierarchy with orange accent.",
    Component: ConceptB,
  },
  {
    id: "C",
    name: "Neon Split",
    desc: "Bold dark card with gradient accent bar. Pace + time get equal billing with distance. High contrast, shareable.",
    Component: ConceptC,
  },
];

export default function RunningStatsOverlay() {
  const [active, setActive] = useState(0);
  const ActiveConcept = concepts[active].Component;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f5f5f0",
        fontFamily: "'DM Sans', sans-serif",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "32px 16px",
      }}
    >
      <link
        href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,500;0,9..40,700;0,9..40,800;1,9..40,400&family=DM+Mono:wght@400;500&display=swap"
        rel="stylesheet"
      />

      <h1
        style={{
          fontSize: 14,
          fontWeight: 700,
          letterSpacing: "0.15em",
          color: "#999",
          textTransform: "uppercase",
          marginBottom: 24,
        }}
      >
        Running Stats Overlay — 3 Concepts
      </h1>

      {/* Tab bar */}
      <div
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 32,
          background: "#e8e8e3",
          borderRadius: 12,
          padding: 4,
        }}
      >
        {concepts.map((c, i) => (
          <button
            key={c.id}
            onClick={() => setActive(i)}
            style={{
              padding: "10px 20px",
              borderRadius: 10,
              border: "none",
              cursor: "pointer",
              fontSize: 13,
              fontWeight: 600,
              fontFamily: "'DM Sans', sans-serif",
              transition: "all 0.2s ease",
              background: active === i ? "#1a1a1a" : "transparent",
              color: active === i ? "#fff" : "#888",
            }}
          >
            {c.id}. {c.name}
          </button>
        ))}
      </div>

      {/* Description */}
      <p
        style={{
          fontSize: 13,
          color: "#888",
          textAlign: "center",
          maxWidth: 400,
          lineHeight: 1.6,
          marginBottom: 28,
        }}
      >
        {concepts[active].desc}
      </p>

      {/* Phone frame */}
      <div
        style={{
          width: 375,
          minHeight: 500,
          background:
            active === 0
              ? "linear-gradient(180deg, #2d5a3d 0%, #1a3525 50%, #0d1f15 100%)"
              : active === 1
              ? "linear-gradient(180deg, #f0ebe3 0%, #e8e3db 100%)"
              : "#111",
          borderRadius: 32,
          padding: "40px 16px",
          display: "flex",
          justifyContent: "center",
          alignItems: "flex-start",
          boxShadow: "0 20px 60px rgba(0,0,0,0.15)",
          border: "1px solid rgba(0,0,0,0.08)",
        }}
      >
        <ActiveConcept />
      </div>

      {/* Design notes */}
      <div
        style={{
          marginTop: 32,
          maxWidth: 420,
          background: "#fff",
          borderRadius: 16,
          padding: "20px 24px",
          border: "1px solid #e8e8e3",
        }}
      >
        <div
          style={{
            fontSize: 11,
            fontWeight: 700,
            color: "#bbb",
            letterSpacing: "0.12em",
            marginBottom: 10,
          }}
        >
          DESIGN RATIONALE
        </div>
        {active === 0 && (
          <div style={{ fontSize: 13, color: "#666", lineHeight: 1.7 }}>
            <strong>Glass Slab</strong> borrows from Strava's latest direction — stats co-exist with the map, not replacing it. The frosted card creates depth while keeping the route visible. The single hero metric (distance) dominates, with secondary stats compressed into a scannable row. Best for: photo/map backgrounds on IG Stories.
          </div>
        )}
        {active === 1 && (
          <div style={{ fontSize: 13, color: "#666", lineHeight: 1.7 }}>
            <strong>Clipboard Card</strong> is closest to your original sketches — the tab at top mirrors the clipboard shape you drew. Each stat gets its own row for easy scanning. The dashed divider and mono font give it a "training log" feel. Best for: data-dense sharing where every metric matters equ