import React, { useState } from "react";
import styles from "./CommentTable.module.css";
import { format, parseISO } from "date-fns";

const PAGE_SIZE = 10;

const BADGE = {
  positive: { color: "#2dce89", bg: "rgba(45,206,137,0.1)", border: "rgba(45,206,137,0.25)", label: "Positive" },
  negative: { color: "#ff3d5a", bg: "rgba(255,61,90,0.1)", border: "rgba(255,61,90,0.25)", label: "Negative" },
  neutral: { color: "#f4a832", bg: "rgba(244,168,50,0.1)", border: "rgba(244,168,50,0.25)", label: "Neutral" },
};

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
  const col = score >= 0.05 ? "#2dce89" : score <= -0.05 ? "#ff3d5a" : "#f4a832";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{
        width: 60, height: 4, background: "#1e1e28",
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

export default function CommentTable({ comments = [], activeTab }) {
  const [page, setPage] = useState(0);
  const [sort, setSort] = useState("likes"); // "likes" | "score" | "date"

  // Reset page when tab or sort changes
  const handleSort = (s) => { setSort(s); setPage(0); };

  const sorted = [...comments].sort((a, b) => {
    if (sort === "likes") return (b.likeCount || 0) - (a.likeCount || 0);
    if (sort === "score") return (b.sentiment?.score || 0) - (a.sentiment?.score || 0);
    if (sort === "date") return (b.publishedAt || "").localeCompare(a.publishedAt || "");
    return 0;
  });

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);
  const slice = sorted.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE);

  if (!comments.length) {
    return (
      <div className={styles.empty}>
        No {activeTab === "all" ? "" : activeTab} comments found.
      </div>
    );
  }

  return (
    <div className={styles.wrapper}>
      {/* Sort controls */}
      <div className={styles.sortRow}>
        <span className={styles.count}>{comments.length} comments</span>
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
              <div className={styles.author}>{c.author}</div>

              <p className={styles.text}>
                {c.commentUrl ? (
                  <a
                    href={c.commentUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {c.text}
                  </a>
                ) : (
                  c.text
                )}
              </p>

              {/* {c.commentUrl && (
                <a href={c.commentUrl}
                target="_blank"
                rel="noopener noreferrer"
                className= {styles.text}
                >
                  {c.text}
                </a>
              )} */}
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
                {c.publishedAt && (
                  <span className={styles.metaItem}>
                    {format(parseISO(c.publishedAt), "MMM d, yyyy")}
                  </span>
                )}
                {c.likeCount > 0 && (
                  <span className={styles.metaItem}>
                    👍 {c.likeCount.toLocaleString()}
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
