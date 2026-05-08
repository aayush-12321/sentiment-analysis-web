/**
 * components/charts/PostCommentComparisonBar.jsx
 * Grouped bar chart comparing Reddit Post sentiment vs Comment sentiment.
 */
import React from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Cell,
} from "recharts";

const POST_COLORS    = { Positive: "#f59e0b", Negative: "#ef4444", Neutral: "#6b7280" };
const COMMENT_COLORS = { Positive: "#7c3aed", Negative: "#db2777", Neutral: "#0891b2" };

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "#12121c",
      border: "1px solid #2f2f3d",
      borderRadius: 10,
      padding: "10px 16px",
      fontSize: 13,
      color: "#ede8d8",
      boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
    }}>
      <div style={{ fontWeight: 700, marginBottom: 8, color: "#fff", fontSize: 14 }}>
        {label}
      </div>
      {payload.map((p) => (
        <div key={p.name} style={{ color: p.fill, marginBottom: 3, display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{
            display: "inline-block", width: 8, height: 8,
            borderRadius: "50%", background: p.fill, flexShrink: 0,
          }} />
          <span style={{ color: "#a0a0b8" }}>{p.name}:</span>
          <strong style={{ color: "#fff" }}>{p.value}%</strong>
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
      name:        "Positive",
      "Posts %":   postSent?.positivePercent    ?? 0,
      "Comments %": commentSent?.positivePercent ?? 0,
    },
    {
      name:        "Negative",
      "Posts %":   postSent?.negativePercent    ?? 0,
      "Comments %": commentSent?.negativePercent ?? 0,
    },
    {
      name:        "Neutral",
      "Posts %":   postSent?.neutralPercent    ?? 0,
      "Comments %": commentSent?.neutralPercent ?? 0,
    },
  ];

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} barCategoryGap="30%" barGap={4}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" vertical={false} />
        <XAxis
          dataKey="name"
          tick={{ fill: "#8a8699", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: "#8a8699", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          unit="%"
          domain={[0, 100]}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(v) => (
            <span style={{ color: "#8a8699", fontSize: 12 }}>{v}</span>
          )}
        />
        <Bar
          dataKey="Posts %"
          radius={[4, 4, 0, 0]}
          maxBarSize={32}
        >
          {data.map((entry) => (
            <Cell
              key={entry.name}
              fill={POST_COLORS[entry.name] || "#f59e0b"}
            />
          ))}
        </Bar>
        <Bar
          dataKey="Comments %"
          radius={[4, 4, 0, 0]}
          maxBarSize={32}
        >
          {data.map((entry) => (
            <Cell
              key={entry.name}
              fill={COMMENT_COLORS[entry.name] || "#7c3aed"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
