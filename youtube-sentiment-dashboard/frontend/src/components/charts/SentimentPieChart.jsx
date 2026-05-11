import React from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = {
  positive: "#22c77c",
  negative: "#f0364f",
  neutral:  "#e09e28",
};

const RADIAN = Math.PI / 180;

function CustomLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent }) {
  if (percent < 0.06) return null;
  const r = innerRadius + (outerRadius - innerRadius) * 0.55;
  const x = cx + r * Math.cos(-midAngle * RADIAN);
  const y = cy + r * Math.sin(-midAngle * RADIAN);
  return (
    <text
      x={x} y={y}
      fill="#fff"
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={12}
      fontWeight={600}
      fontFamily="Inter, sans-serif"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { name, value } = payload[0];
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
      <strong style={{ color: COLORS[name], textTransform: "capitalize" }}>{name}</strong>
      <div style={{ color: "var(--tooltip-sub)", marginTop: 2 }}>{value.toLocaleString()} items</div>
    </div>
  );
}

export default function SentimentPieChart({ summary }) {
  const data = [
    { name: "positive", value: summary.positive },
    { name: "negative", value: summary.negative },
    { name: "neutral",  value: summary.neutral  },
  ].filter((d) => d.value > 0);

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={88}
          paddingAngle={3}
          dataKey="value"
          labelLine={false}
          label={CustomLabel}
          animationBegin={0}
          animationDuration={800}
        >
          {data.map((entry) => (
            <Cell key={entry.name} fill={COLORS[entry.name]} stroke="transparent" />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(value) => (
            <span style={{ color: "var(--chart-subtext)", fontSize: 12, textTransform: "capitalize" }}>
              {value}
            </span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
