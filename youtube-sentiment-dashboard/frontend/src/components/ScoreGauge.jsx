import React, { useEffect, useRef } from "react";
import styles from "./ScoreGauge.module.css";

/**
 * Animated SVG semi-circle gauge showing avg compound score (−1 to +1).
 */
export default function ScoreGauge({ score = 0 }) {
  const arcRef = useRef(null);

  const norm    = (score + 1) / 2;
  const radius  = 72;
  const cx      = 100;
  const cy      = 96;
  const strokeW = 12;
  const circum  = Math.PI * radius;
  const offset  = circum * (1 - norm);

  const label = score >= 0.05 ? "Positive" : score <= -0.05 ? "Negative" : "Neutral";
  const color = score >= 0.05 ? "#22c77c"  : score <= -0.05 ? "#f0364f"  : "#e09e28";

  useEffect(() => {
    if (!arcRef.current) return;
    arcRef.current.style.strokeDashoffset = circum;
    requestAnimationFrame(() => {
      arcRef.current.style.transition = "stroke-dashoffset 1.2s cubic-bezier(0.22,1,0.36,1)";
      arcRef.current.style.strokeDashoffset = offset;
    });
  }, [score, circum, offset]);

  return (
    <div className={styles.wrapper}>
      <svg viewBox="0 0 200 110" className={styles.svg}>
        {/* Track arc */}
        <path
          d={describeArc(cx, cy, radius)}
          fill="none"
          stroke="var(--border-light)"
          strokeWidth={strokeW}
          strokeLinecap="round"
        />
        {/* Value arc */}
        <path
          ref={arcRef}
          d={describeArc(cx, cy, radius)}
          fill="none"
          stroke={color}
          strokeWidth={strokeW}
          strokeLinecap="round"
          strokeDasharray={circum}
          strokeDashoffset={circum}
          style={{ filter: `drop-shadow(0 0 6px ${color}55)` }}
        />
        {/* Center score text */}
        <text x={cx} y={cy - 8} textAnchor="middle" className={styles.scoreText} fill={color}>
          {score >= 0 ? "+" : ""}{score.toFixed(3)}
        </text>
        <text x={cx} y={cy + 14} textAnchor="middle" className={styles.labelText} fill="var(--text-muted)">
          {label}
        </text>
        {/* Min / Max labels */}
        <text x={19} y={cy + 20} className={styles.minmax} fill="var(--chart-text)">−1</text>
        <text x={178} y={cy + 20} className={styles.minmax} fill="var(--chart-text)">+1</text>
      </svg>

      <div className={styles.legend}>
        <span style={{ color: "#f0364f" }}>● Negative</span>
        <span style={{ color: "#e09e28" }}>● Neutral</span>
        <span style={{ color: "#22c77c" }}>● Positive</span>
      </div>
    </div>
  );
}

function describeArc(cx, cy, r) {
  const startX = cx - r;
  const startY = cy;
  const endX   = cx + r;
  const endY   = cy;
  return `M ${startX} ${startY} A ${r} ${r} 0 0 1 ${endX} ${endY}`;
}
