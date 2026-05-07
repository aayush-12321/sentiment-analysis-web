/**
 * components/charts/SourceComparisonBar.jsx
 * Grouped bar chart comparing YouTube vs Reddit sentiment distributions.
 */
import React from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";

const COLORS = {
  youtube: { positive: "#2dce89", negative: "#ff3d5a", neutral: "#f4a832" },
  reddit:  { positive: "#45a8f0", negative: "#ff7043", neutral: "#ab7ef6" },
};

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "#17171f", border: "1px solid #2f2f3d",
      borderRadius: 10, padding: "10px 16px", fontSize: 13, color: "#ede8d8",
    }}>
      <div style={{ fontWeight: 600, marginBottom: 6, color: "#fff" }}>{label}</div>
      {payload.map((p) => (
        <div key={p.name} style={{ color: p.fill, marginBottom: 2 }}>
          {p.name}: <strong>{p.value}%</strong>
        </div>
      ))}
    </div>
  );
}

export default function SourceComparisonBar({ youtubeResult, redditResult }) {
  const yt = youtubeResult?.summary;
  const rd = redditResult?.summary;

  if (!yt && !rd) return null;

  const data = [
    {
      name: "Positive",
      "YouTube %": yt?.positivePercent ?? 0,
      "Reddit %":  rd?.positivePercent ?? 0,
    },
    {
      name: "Negative",
      "YouTube %": yt?.negativePercent ?? 0,
      "Reddit %":  rd?.negativePercent ?? 0,
    },
    {
      name: "Neutral",
      "YouTube %": yt?.neutralPercent ?? 0,
      "Reddit %":  rd?.neutralPercent ?? 0,
    },
  ];

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} barCategoryGap="30%" barGap={4}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a38" />
        <XAxis
          dataKey="name"
          tick={{ fill: "#8a8699", fontSize: 12 }}
          axisLine={false} tickLine={false}
        />
        <YAxis
          tick={{ fill: "#8a8699", fontSize: 11 }}
          axisLine={false} tickLine={false}
          unit="%" domain={[0, 100]}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
        <Legend
          iconType="circle" iconSize={8}
          formatter={(v) => (
            <span style={{ color: "#8a8699", fontSize: 12 }}>{v}</span>
          )}
        />
        <Bar dataKey="YouTube %" fill="#a78bfa" radius={[4, 4, 0, 0]} maxBarSize={32} />
        <Bar dataKey="Reddit %"  fill="#38bdf8" radius={[4, 4, 0, 0]} maxBarSize={32} />
      </BarChart>
    </ResponsiveContainer>
  );
}
