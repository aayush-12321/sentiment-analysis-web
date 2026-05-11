import React from "react";

export default function LoadingState({ keyword }) {
  const steps = [
    "Searching YouTube videos",
    "Fetching comments",
    "Running RoBERTa/VADER analysis",
    "Building your dashboard",
  ];

  return (
    <div style={{
      textAlign: "center",
      padding: "80px 32px",
      animation: "fadeIn 0.3s ease both",
    }}>
      <div style={{ position: "relative", width: 64, height: 64, margin: "0 auto 28px" }}>
        {[
          { color: "#5b52f0", inset: 0,  dur: "0.9s" },
          { color: "#22c77c", inset: 10, dur: "1.2s" },
          { color: "#f0364f", inset: 20, dur: "1.6s" },
        ].map((ring, i) => (
          <div key={i} style={{
            position: "absolute",
            inset: ring.inset,
            border: "2px solid transparent",
            borderTopColor: ring.color,
            borderRadius: "50%",
            animation: `spin ${ring.dur} linear infinite`,
          }} />
        ))}
      </div>

      <h3 style={{
        fontFamily: "var(--font-display)",
        fontSize: 19,
        fontWeight: 700,
        color: "var(--text-primary)",
        marginBottom: 8,
        letterSpacing: "-0.02em",
      }}>
        Analysing "{keyword}"
      </h3>

      <p style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 32, lineHeight: 1.6 }}>
        Fetching data and running sentiment analysis…
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 10, alignItems: "center" }}>
        {steps.map((step, i) => (
          <div key={step} style={{
            fontSize: 12,
            color: "var(--text-muted)",
            display: "flex",
            alignItems: "center",
            gap: 10,
            animation: `fadeUp 0.4s ${0.1 + i * 0.15}s ease both`,
            fontWeight: 500,
          }}>
            <span style={{
              width: 6,
              height: 6,
              background: "var(--text-muted)",
              borderRadius: "50%",
              animation: `pulse 1.6s ${i * 0.35}s ease infinite`,
              flexShrink: 0,
            }} />
            {step}
          </div>
        ))}
      </div>
    </div>
  );
}
