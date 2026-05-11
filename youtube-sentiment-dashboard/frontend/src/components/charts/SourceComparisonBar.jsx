/**
 * components/charts/SourceComparisonBar.jsx
 * Grouped bar chart comparing YouTube vs Reddit sentiment distributions.
 */
import React from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";

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
      <div style={{ fontWeight: 700, marginBottom: 6, color: "var(--tooltip-text)" }}>{label}</div>
      {payload.map((p) => (
        <div key={p.name} style={{ color: p.fill, marginBottom: 3, fontWeight: 500 }}>
          {p.name}: <strong style={{ color: "var(--tooltip-text)" }}>{p.value}%</strong>
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
        <Bar dataKey="YouTube %" fill="#5b52f0" radius={[4, 4, 0, 0]} maxBarSize={32} />
        <Bar dataKey="Reddit %"  fill="#22b8c7" radius={[4, 4, 0, 0]} maxBarSize={32} />
      </BarChart>
    </ResponsiveContainer>
  );
}
