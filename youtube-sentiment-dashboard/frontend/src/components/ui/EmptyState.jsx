import React, { useMemo } from "react";

const EXAMPLES = ["Nike", "Apple", "Tesla", "Spotify", "OpenAI", "Samsung"];
const PALETTE  = ["#6c63ff", "#2dce89", "#ff3d5a", "#f4a832", "#2f2f3d"];

export default function EmptyState() {
  const dots = useMemo(() =>
    Array.from({ length: 21 }).map(() => ({
      color:   PALETTE[Math.floor(Math.random() * PALETTE.length)],
      opacity: 0.3 + Math.random() * 0.7,
      dur:     1 + Math.random() * 2,
      delay:   Math.random(),
    })),
  []);

  return (
    <div style={{ textAlign: "center", padding: "72px 32px", animation: "fadeUp 0.5s ease both" }}>
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(7, 1fr)",
        gap: 8,
        width: 120,
        margin: "0 auto 36px",
      }}>
        {dots.map((d, i) => (
          <div key={i} style={{
            width: 8, height: 8,
            borderRadius: "50%",
            background: d.color,
            opacity: d.opacity,
            animation: `pulse ${d.dur}s ${d.delay}s ease infinite`,
          }} />
        ))}
      </div>

      <h2 style={{
        fontFamily: "Syne, sans-serif",
        fontSize: 22, fontWeight: 700,
        color: "#ede8d8",
        marginBottom: 10,
        letterSpacing: "-0.03em",
      }}>
        Enter a brand to get started
      </h2>

      <p style={{ color: "#8a8699", fontSize: 14, marginBottom: 28 }}>
        We'll analyse YouTube comments and surface sentiment insights instantly.
      </p>

      <div style={{ display: "flex", gap: 8, justifyContent: "center", flexWrap: "wrap" }}>
        {EXAMPLES.map((brand) => (
          <span key={brand} style={{
            fontSize: 12,
            padding: "5px 13px",
            borderRadius: 100,
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            color: "var(--text-secondary)",
          }}>
            {brand}
          </span>
        ))}
      </div>
    </div>
  );
}
