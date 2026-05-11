import React from "react";

export default function ErrorBanner({ message }) {
  return (
    <div style={{
      background: "var(--negative-bg)",
      border: "1px solid var(--negative-border)",
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
        <p style={{ fontWeight: 600, color: "var(--negative)", marginBottom: 4, fontSize: 14 }}>
          Analysis Failed
        </p>
        <p style={{ color: "var(--text-secondary)", fontSize: 14, lineHeight: 1.5 }}>{message}</p>
      </div>
    </div>
  );
}
