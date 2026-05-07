import React, { useEffect, useRef } from "react";
import styles from "./ScoreGauge.module.css";

/**
 * Animated SVG semi-circle gauge showing avg compound score (−1 to +1).
 */
export default function ScoreGauge({ score = 0 }) {
  const arcRef = useRef(null);

  // Normalize −1…+1 → 0…1
  const norm    = (score + 1) / 2;
  const radius  = 72;
  const cx      = 100;
  const cy      = 96;
  const strokeW = 12;
  const circum  = Math.PI * radius;          // half-circle circumference
  const offset  = circum * (1 - norm);       // dash offset

  const label  = score >= 0.05 ? "Positive" : score <= -0.05 ? "Negative" : "Neutral";
  const color  = score >= 0.05 ? "#2dce89"  : score <= -0.05 ? "#ff3d5a"  : "#f4a832";

  useEffect(() => {
    if (!arcRef.current) return;
    arcRef.current.style.strokeDashoffset = circum; // start collapsed
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
          stroke="#1e1e28"
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
          style={{ filter: `drop-shadow(0 0 8px ${color}66)` }}
        />
        {/* Center score text */}
        <text x={cx} y={cy - 8} textAnchor="middle" className={styles.scoreText} fill={color}>
          {score >= 0 ? "+" : ""}{score.toFixed(3)}
        </text>
        <text x={cx} y={cy + 14} textAnchor="middle" className={styles.labelText} fill="#8a8699">
          {label}
        </text>
        {/* Min / Max labels */}
        <text x={19} y={cy + 20} className={styles.minmax} fill="#4e4b58">−1</text>
        <text x={178} y={cy + 20} className={styles.minmax} fill="#4e4b58">+1</text>
      </svg>

      <div className={styles.legend}>
        <span style={{ color: "#ff3d5a" }}>● Negative</span>
        <span style={{ color: "#f4a832" }}>● Neutral</span>
        <span style={{ color: "#2dce89" }}>● Positive</span>
      </div>
    </div>
  );
}

function describeArc(cx, cy, r) {
  // Left to right semi-circle (bottom half)
  const startX = cx - r;
  const startY = cy;
  const endX   = cx + r;
  const endY   = cy;
  return `M ${startX} ${startY} A ${r} ${r} 0 0 1 ${endX} ${endY}`;
}
