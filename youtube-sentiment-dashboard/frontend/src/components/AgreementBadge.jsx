/**
 * components/AgreementBadge.jsx
 * Shows the sentiment agreement score between YouTube and Reddit.
 */
import React from "react";
import styles from "./AgreementBadge.module.css";

export default function AgreementBadge({ score }) {
  if (score === undefined || score === null) return null;

  const level =
    score >= 75 ? "high" :
    score >= 50 ? "medium" : "low";

  const label =
    score >= 75 ? "Strong Agreement" :
    score >= 50 ? "Moderate Agreement" : "Low Agreement";

  return (
    <div className={`${styles.badge} ${styles[level]}`}>
      <div className={styles.iconWrap}>
        <svg viewBox="0 0 20 20" fill="none" className={styles.icon}>
          <path d="M10 2C5.6 2 2 5.6 2 10s3.6 8 8 8 8-3.6 8-8-3.6-8-8-8z"
            stroke="currentColor" strokeWidth="1.5"/>
          <path d="M6.5 10l2.5 2.5 4-4.5" stroke="currentColor"
            strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>
      <div className={styles.content}>
        <div className={styles.scoreRow}>
          <span className={styles.scoreNum}>{score.toFixed(0)}%</span>
          <span className={styles.scoreLabel}>{label}</span>
        </div>
        <div className={styles.sub}>between YouTube &amp; Reddit</div>
      </div>
      <div className={styles.barTrack}>
        <div className={styles.barFill} style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}
