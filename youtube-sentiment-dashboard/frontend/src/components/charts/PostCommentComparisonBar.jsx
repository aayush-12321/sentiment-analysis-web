/**
 * components/charts/PostCommentComparisonBar.jsx
 * Grouped bar chart comparing Reddit Post vs Comment sentiment.
 */
import React from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Cell,
} from "recharts";

const POST_COLORS    = { Positive: "#22c77c", Negative: "#f0364f", Neutral: "#e09e28" };
const COMMENT_COLORS = { Positive: "#5b52f0", Negative: "#e0407a", Neutral: "#22b8c7" };

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "var(--tooltip-bg)",
      border: "1px solid var(--tooltip-border)",
      borderRadius: 10,
      padding: "10px 16px",
      fontSize: 13,
      color: "var(--tooltip-text)",
      boxShadow: "var(--shadow-tooltip)",
    }}>
      <div style={{ fontWeight: 700, marginBottom: 8, fontSize: 14 }}>{label}</div>
      {payload.map((p) => (
        <div key={p.name} style={{ marginBottom: 3, display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{
            display: "inline-block", width: 8, height: 8,
            borderRadius: "50%", background: p.fill, flexShrink: 0,
          }} />
          <span style={{ color: "var(--tooltip-sub)", fontWeight: 500 }}>{p.name}:</span>
          <strong style={{ color: "var(--tooltip-text)" }}>{p.value}%</strong>
        </div>
      ))}
    </div>
  );
}

export default function PostCommentComparisonBar({ redditResult }) {
  const postSent    = redditResult?.post_sentiment;
  const commentSent = redditResult?.comment_sentiment;

  if (!postSent && !commentSent) return null;
  if ((postSent?.total ?? 0) === 0 && (commentSent?.total ?? 0) === 0) return null;

  const data = [
    {
      name:          "Positive",
      "Posts %":     postSent?.positivePercent    ?? 0,
      "Comments %":  commentSent?.positivePercent ?? 0,
    },
    {
      name:          "Negative",
      "Posts %":     postSent?.negativePercent    ?? 0,
      "Comments %":  commentSent?.negativePercent ?? 0,
    },
    {
      name:          "Neutral",
      "Posts %":     postSent?.neutralPercent    ?? 0,
      "Comments %":  commentSent?.neutralPercent ?? 0,
    },
  ];

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} barCategoryGap="30%" barGap={4}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" vertical={false} />
        <XAxis
          dataKey="name"
          tick={{ fill: "var(--chart-subtext)", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: "var(--chart-text)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          unit="%"
          domain={[0, 100]}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--bg-hover)" }} />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(v) => (
            <span style={{ color: "var(--chart-subtext)", fontSize: 12 }}>{v}</span>
          )}
        />
        <Bar dataKey="Posts %" radius={[4, 4, 0, 0]} maxBarSize={32}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={POST_COLORS[entry.name] || "#22c77c"} />
          ))}
        </Bar>
        <Bar dataKey="Comments %" radius={[4, 4, 0, 0]} maxBarSize={32}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={COMMENT_COLORS[entry.name] || "#5b52f0"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
