/**
 * components/SourceBreakdownCards.jsx
 * Side-by-side YouTube vs Reddit sentiment breakdown cards.
 */
import React from "react";
import styles from "./SourceBreakdownCards.module.css";

function SourceCard({ title, icon, iconColor, summary, itemLabel }) {
  if (!summary || summary.total === 0) {
    return (
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.sourceIcon} style={{ color: iconColor }}>{icon}</span>
          <span className={styles.sourceTitle}>{title}</span>
        </div>
        <p className={styles.empty}>No data available</p>
      </div>
    );
  }

  const bars = [
    { label: "Positive", pct: summary.positivePercent, color: "var(--positive)", count: summary.positive },
    { label: "Negative", pct: summary.negativePercent, color: "var(--negative)", count: summary.negative },
    { label: "Neutral",  pct: summary.neutralPercent,  color: "var(--neutral)",  count: summary.neutral },
  ];

  const dominant = bars.reduce((a, b) => (a.pct >= b.pct ? a : b));

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <span className={styles.sourceIcon} style={{ color: iconColor }}>{icon}</span>
        <div>
          <span className={styles.sourceTitle}>{title}</span>
          <span className={styles.sourceMeta}>
            {summary.total.toLocaleString()} {itemLabel} analysed
          </span>
        </div>
        <span
          className={styles.dominantBadge}
          style={{
            background:
              dominant.label === "Positive" ? "rgba(45,206,137,0.15)" :
              dominant.label === "Negative" ? "rgba(255,61,90,0.15)" :
              "rgba(244,168,50,0.15)",
            color:
              dominant.label === "Positive" ? "var(--positive)" :
              dominant.label === "Negative" ? "var(--negative)" :
              "var(--neutral)",
          }}
        >
          {dominant.label}
        </span>
      </div>

      <div className={styles.bars}>
        {bars.map((b) => (
          <div key={b.label} className={styles.barRow}>
            <div className={styles.barMeta}>
              <span className={styles.barLabel}>{b.label}</span>
              <span className={styles.barCount}>{b.pct}%</span>
            </div>
            <div className={styles.barTrack}>
              <div
                className={styles.barFill}
                style={{ width: `${b.pct}%`, background: b.color }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className={styles.avgScore}>
        Avg score: <strong>{summary.avg_score > 0 ? "+" : ""}{summary.avg_score}</strong>
      </div>
    </div>
  );
}

export default function SourceBreakdownCards({ youtubeResult, redditResult }) {
  // For Reddit: use combined summary (posts + comments), fall back to post-only
  const redditSummary = redditResult?.summary;

  // Determine label for Reddit items
  const redditItemLabel = (() => {
    const pc = redditResult?.summary?.totalPosts    ?? 0;
    const cc = redditResult?.summary?.totalComments ?? 0;
    if (pc > 0 && cc > 0) return `posts & ${cc} comments`;
    if (cc > 0) return "comments";
    return "posts";
  })();

  return (
    <div className={styles.grid}>
      <SourceCard
        title="YouTube"
        icon="▶"
        iconColor="#ff0000"
        summary={youtubeResult?.summary}
        itemLabel="comments"
      />
      <SourceCard
        title="Reddit"
        icon="🔴"
        iconColor="#ff4500"
        summary={redditSummary}
        itemLabel={redditItemLabel}
      />
    </div>
  );
}
