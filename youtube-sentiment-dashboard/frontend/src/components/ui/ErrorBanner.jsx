import React from "react";

export default function ErrorBanner({ message }) {
  return (
    <div style={{
      background: "rgba(255,61,90,0.06)",
      border: "1px solid rgba(255,61,90,0.3)",
      borderRadius: 14,
      padding: "20px 24px",
      display: "flex",
      alignItems: "flex-start",
      gap: 14,
      animation: "fadeUp 0.3s ease both",
      margin: "16px 0",
    }}>
      <span style={{ fontSize: 20, flexShrink: 0 }}>⚠</span>
      <div>
        <p style={{ fontWeight: 600, color: "#ff3d5a", marginBottom: 4, fontSize: 14 }}>
          Analysis Failed
        </p>
        <p style={{ color: "#8a8699", fontSize: 14, lineHeight: 1.5 }}>{message}</p>
      </div>
    </div>
  );
}
