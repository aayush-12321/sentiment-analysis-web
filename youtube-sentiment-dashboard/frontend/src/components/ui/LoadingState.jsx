import React from "react";

export default function LoadingState({ keyword }) {
  const steps = [
    "Searching YouTube videos",
    "Fetching comments",
    "Running VADER sentiment analysis",
    "Building your dashboard",
  ];

  return (
    <div style={{
      textAlign: "center",
      padding: "80px 32px",
      animation: "fadeIn 0.3s ease both",
    }}>
      <div style={{ position: "relative", width: 72, height: 72, margin: "0 auto 28px" }}>
        {[
          { color: "#6c63ff", inset: 0,  dur: "0.9s" },
          { color: "#2dce89", inset: 10, dur: "1.2s" },
          { color: "#ff3d5a", inset: 20, dur: "1.6s" },
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
        fontFamily: "Syne, sans-serif",
        fontSize: 20, fontWeight: 700,
        color: "#ede8d8", marginBottom: 10,
        letterSpacing: "-0.02em",
      }}>
        Analysing "{keyword}"
      </h3>
      <p style={{ color: "#8a8699", fontSize: 14, marginBottom: 32 }}>
        Fetching YouTube comments and running VADER sentiment analysis…
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: 10, alignItems: "center" }}>
        {steps.map((step, i) => (
          <div key={step} style={{
            fontSize: 12, color: "#4e4b58",
            display: "flex", alignItems: "center", gap: 10,
            animation: `fadeUp 0.4s ${0.1 + i * 0.15}s ease both`,
          }}>
            <span style={{
              width: 6, height: 6, background: "#4e4b58",
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
