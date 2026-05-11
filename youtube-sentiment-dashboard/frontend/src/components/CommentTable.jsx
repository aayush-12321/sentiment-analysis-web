import React, { useState } from "react";
import styles from "./CommentTable.module.css";
import { format, parseISO, isValid } from "date-fns";

const PAGE_SIZE = 10;

/* ── Sentiment badge colours — kept vivid, work on both themes ── */
const BADGE = {
  positive: { color: "var(--positive)", bg: "var(--positive-bg)", border: "var(--positive-border)", label: "Positive" },
  negative: { color: "var(--negative)", bg: "var(--negative-bg)", border: "var(--negative-border)", label: "Negative" },
  neutral:  { color: "var(--neutral)",  bg: "var(--neutral-bg)",  border: "var(--neutral-border)",  label: "Neutral"  },
};

/* ── Source chip colours — vivid but not opaque-white-dependent ── */
const SOURCE_BADGE = {
  youtube:        { label: "YT",     color: "#ef4444", bg: "rgba(239,68,68,0.10)"    },
  reddit:         { label: "Reddit", color: "#f97316", bg: "rgba(249,115,22,0.10)"   },
  reddit_post:    { label: "Post",   color: "#d97706", bg: "rgba(217,119,6,0.10)"    },
  reddit_comment: { label: "Cmt",    color: "var(--accent-light)", bg: "var(--accent-bg)" },
};

function SourceBadge({ source }) {
  const s = SOURCE_BADGE[source];
  if (!s) return null;
  return (
    <span style={{
      fontSize: 10, fontWeight: 700, padding: "2px 7px",
      borderRadius: 100, letterSpacing: "0.05em",
      color: s.color, background: s.bg, marginRight: 4,
    }}>
      {s.label}
    </span>
  );
}

function safeFormatDate(dateStr) {
  if (!dateStr) return null;
  try {
    const d = parseISO(dateStr);
    return isValid(d) ? format(d, "MMM d, yyyy") : null;
  } catch {
    return null;
  }
}

function SentimentBadge({ label }) {
  const s = BADGE[label] || BADGE.neutral;
  return (
    <span style={{
      fontSize: 11, fontWeight: 600, padding: "3px 9px",
      borderRadius: 100, letterSpacing: "0.04em",
      color: s.color, background: s.bg, border: `1px solid ${s.border}`,
    }}>
      {s.label}
    </span>
  );
}

function ScoreBar({ score }) {
  const pct = ((score + 1) / 2) * 100;
  const col =
    score >= 0.05  ? "var(--positive)" :
    score <= -0.05 ? "var(--negative)" :
    "var(--neutral)";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{
        width: 60, height: 4,
        background: "var(--border)",
        borderRadius: 2, overflow: "hidden", flexShrink: 0,
      }}>
        <div style={{ width: `${pct}%`, height: "100%", background: col, borderRadius: 2 }} />
      </div>
      <span style={{ fontSize: 11, color: col, fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>
        {score >= 0 ? "+" : ""}{score.toFixed(3)}
      </span>
    </div>
  );
}

export default function CommentTable({ comments = [], activeTab, itemLabel }) {
  const [page, setPage] = useState(0);
  const [sort, setSort] = useState("likes"); // "likes" | "score" | "date"

  const handleSort = (s) => { setSort(s); setPage(0); };

  const sorted = [...comments].sort((a, b) => {
    if (sort === "likes") return (b.likeCount || 0) - (a.likeCount || 0);
    if (sort === "score") return (b.sentiment?.score || 0) - (a.sentiment?.score || 0);
    if (sort === "date")  return (b.publishedAt || "").localeCompare(a.publishedAt || "");
    return 0;
  });

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);
  const slice = sorted.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE);

  if (!comments.length) {
    return (
      <div className={styles.empty}>
        No {activeTab === "all" ? "" : activeTab} {itemLabel || "comments"} found.
      </div>
    );
  }

  return (
    <div className={styles.wrapper}>
      {/* Sort controls */}
      <div className={styles.sortRow}>
        <span className={styles.count}>{comments.length} {itemLabel || "items"}</span>
        <div className={styles.sortBtns}>
          <span className={styles.sortLabel}>Sort by:</span>
          {["likes", "score", "date"].map((s) => (
            <button
              key={s}
              className={`${styles.sortBtn} ${sort === s ? styles.sortActive : ""}`}
              onClick={() => handleSort(s)}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Comment rows */}
      <div className={styles.list}>
        {slice.map((c, i) => (
          <div key={c.commentId || i} className={styles.row}>
            {/* Left: avatar letter */}
            <div className={styles.avatar}>
              {(c.author || "A").charAt(0).toUpperCase()}
            </div>

            {/* Centre: text + meta */}
            <div className={styles.body}>
              <div className={styles.author}>
                <SourceBadge source={c.source} />
                {c.author}
                {c.subreddit && (
                  <span style={{ fontSize: 10, color: "var(--text-muted)", marginLeft: 6, fontWeight: 500 }}>
                    {c.subreddit}
                  </span>
                )}
              </div>

              <p className={styles.text}>
                {c.url || c.commentUrl ? (
                  <a
                    href={c.url || c.commentUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    style={{ color: "inherit" }}
                  >
                    {c.text || c.title || c.body}
                  </a>
                ) : (
                  c.text || c.title || c.body
                )}
              </p>

              <div className={styles.meta}>
                {c.videoTitle && (
                  <span className={styles.metaItem}>
                    <svg viewBox="0 0 16 16" fill="none" width="12" height="12">
                      <rect x="1" y="3" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.2" />
                      <path d="M6 6l4 2-4 2V6z" fill="currentColor" />
                    </svg>
                    {c.videoTitle.length > 40 ? c.videoTitle.slice(0, 40) + "…" : c.videoTitle}
                  </span>
                )}
                {safeFormatDate(c.publishedAt) && (
                  <span className={styles.metaItem}>
                    {safeFormatDate(c.publishedAt)}
                  </span>
                )}
                {c.likeCount > 0 && (
                  <span className={styles.metaItem}>
                    👍 {c.likeCount.toLocaleString()}
                  </span>
                )}
                {(c.source === "reddit_comment" && c.score !== undefined) && (
                  <span className={styles.metaItem}>
                    ⬆ {c.score}
                  </span>
                )}
              </div>
            </div>

            {/* Right: sentiment badge + score bar */}
            <div className={styles.right}>
              <SentimentBadge label={c.sentiment?.label} />
              <ScoreBar score={c.sentiment?.score || 0} />
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className={styles.pagination}>
          <button
            className={styles.pageBtn}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
          >← Prev</button>
          <span className={styles.pageInfo}>
            {page + 1} / {totalPages}
          </span>
          <button
            className={styles.pageBtn}
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page === totalPages - 1}
          >Next →</button>
        </div>
      )}
    </div>
  );
}
