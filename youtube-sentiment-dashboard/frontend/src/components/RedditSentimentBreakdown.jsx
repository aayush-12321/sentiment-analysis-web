/**
 * components/RedditSentimentBreakdown.jsx
 * Shows Reddit post sentiment vs comment sentiment side-by-side,
 * plus a combined overview card.
 */
import React from "react";
import styles from "./RedditSentimentBreakdown.module.css";

// ── Helpers ────────────────────────────────────────────────────────────────

function pct(val) {
  return typeof val === "number" ? val.toFixed(1) : "0.0";
}

function sentimentColor(label) {
  if (!label) return "var(--neutral)";
  const l = label.toLowerCase();
  if (l === "positive") return "var(--positive, #2dce89)";
  if (l === "negative") return "var(--negative, #ff3d5a)";
  return "var(--neutral, #f4a832)";
}

// ── Mini bar row ───────────────────────────────────────────────────────────

function MiniBar({ label, pctVal, color, count }) {
  return (
    <div className={styles.barRow}>
      <div className={styles.barMeta}>
        <span className={styles.barLabel}>{label}</span>
        <span className={styles.barPct} style={{ color }}>{pct(pctVal)}%</span>
      </div>
      <div className={styles.barTrack}>
        <div
          className={styles.barFill}
          style={{ width: `${Math.min(pctVal || 0, 100)}%`, background: color }}
        />
      </div>
      {count !== undefined && (
        <span className={styles.barCount}>{count}</span>
      )}
    </div>
  );
}

// ── Single panel (posts OR comments) ──────────────────────────────────────

function SentimentPanel({ title, icon, summary, itemLabel, color }) {
  if (!summary || summary.total === 0) {
    return (
      <div className={styles.panel}>
        <div className={styles.panelHeader} style={{ borderColor: color }}>
          <span className={styles.panelIcon}>{icon}</span>
          <span className={styles.panelTitle}>{title}</span>
        </div>
        <p className={styles.empty}>No {itemLabel} analysed</p>
      </div>
    );
  }

  const dominant = summary.dominantSentiment ||
    (summary.positivePercent >= summary.negativePercent &&
     summary.positivePercent >= summary.neutralPercent
      ? "positive"
      : summary.negativePercent >= summary.neutralPercent
      ? "negative"
      : "neutral");

  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader} style={{ borderColor: color }}>
        <span className={styles.panelIcon}>{icon}</span>
        <div className={styles.panelMeta}>
          <span className={styles.panelTitle}>{title}</span>
          <span className={styles.panelCount}>
            {summary.total.toLocaleString()} {itemLabel}
          </span>
        </div>
        <span
          className={styles.dominantBadge}
          style={{ background: `${sentimentColor(dominant)}22`, color: sentimentColor(dominant) }}
        >
          {dominant.charAt(0).toUpperCase() + dominant.slice(1)}
        </span>
      </div>

      <div className={styles.bars}>
        <MiniBar
          label="Positive"
          pctVal={summary.positivePercent}
          color="var(--positive, #2dce89)"
          count={summary.positive}
        />
        <MiniBar
          label="Negative"
          pctVal={summary.negativePercent}
          color="var(--negative, #ff3d5a)"
          count={summary.negative}
        />
        <MiniBar
          label="Neutral"
          pctVal={summary.neutralPercent}
          color="var(--neutral, #f4a832)"
          count={summary.neutral}
        />
      </div>

      <div className={styles.avgScore}>
        Avg score:&nbsp;
        <strong style={{ color: summary.avg_score > 0 ? "var(--positive, #2dce89)" : summary.avg_score < 0 ? "var(--negative, #ff3d5a)" : "var(--neutral, #f4a832)" }}>
          {summary.avg_score > 0 ? "+" : ""}{summary.avg_score}
        </strong>
      </div>
    </div>
  );
}

// ── Combined overview pill row ─────────────────────────────────────────────

function OverviewPills({ totalPosts, totalComments, combined }) {
  const pills = [
    { label: "Posts", value: totalPosts ?? 0,     icon: "📄" },
    { label: "Comments", value: totalComments ?? 0, icon: "💬" },
    { label: "Positive", value: `${pct(combined?.positivePercent)}%`, icon: "👍", color: "var(--positive, #2dce89)" },
    { label: "Negative", value: `${pct(combined?.negativePercent)}%`, icon: "👎", color: "var(--negative, #ff3d5a)" },
    { label: "Neutral",  value: `${pct(combined?.neutralPercent)}%`,  icon: "😐", color: "var(--neutral, #f4a832)"  },
  ];
  return (
    <div className={styles.pills}>
      {pills.map((p) => (
        <div key={p.label} className={styles.pill}>
          <span className={styles.pillIcon}>{p.icon}</span>
          <span className={styles.pillValue} style={p.color ? { color: p.color } : {}}>
            {p.value}
          </span>
          <span className={styles.pillLabel}>{p.label}</span>
        </div>
      ))}
    </div>
  );
}

// ── Main export ────────────────────────────────────────────────────────────

export default function RedditSentimentBreakdown({ redditResult }) {
  if (!redditResult) return null;

  const { post_sentiment, comment_sentiment, summary } = redditResult;

  // If there's no breakdown (old-format result), render nothing
  if (!post_sentiment && !comment_sentiment) return null;

  return (
    <div className={styles.root}>
      <div className={styles.sectionHeader}>
        <span className={styles.rdIcon}>🔴</span>
        <h3 className={styles.sectionTitle}>Reddit Sentiment Breakdown</h3>
      </div>

      {/* Overview pills */}
      <OverviewPills
        totalPosts={summary?.totalPosts}
        totalComments={summary?.totalComments}
        combined={summary}
      />

      {/* Post vs Comment panels */}
      <div className={styles.panelsGrid}>
        <SentimentPanel
          title="Post Titles"
          icon="📄"
          summary={post_sentiment}
          itemLabel="posts"
          color="#ff8c00"
        />
        <SentimentPanel
          title="Comments"
          icon="💬"
          summary={comment_sentiment}
          itemLabel="comments"
          color="#7c3aed"
        />
      </div>
    </div>
  );
}
