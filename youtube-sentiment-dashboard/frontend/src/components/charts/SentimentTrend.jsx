import React from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { format, parseISO } from "date-fns";

const LINE_COLORS = {
  positive: "#22c77c",
  negative: "#f0364f",
  neutral:  "#e09e28",
};

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "var(--tooltip-bg)",
      border: "1px solid var(--tooltip-border)",
      borderRadius: 10,
      padding: "12px 16px",
      fontSize: 13,
      boxShadow: "var(--shadow-tooltip)",
    }}>
      <p style={{ color: "var(--tooltip-sub)", marginBottom: 8, fontSize: 11, fontWeight: 500 }}>
        {label}
      </p>
      {payload.map((p) => (
        <div key={p.dataKey} style={{ display: "flex", justifyContent: "space-between", gap: 16, marginBottom: 4 }}>
          <span style={{ color: LINE_COLORS[p.dataKey] || p.color, textTransform: "capitalize", fontWeight: 500 }}>
            {p.dataKey}
          </span>
          <span style={{ color: "var(--tooltip-text)", fontWeight: 700 }}>{p.value}</span>
        </div>
      ))}
    </div>
  );
}

export default function SentimentTrend({ trend = [] }) {
  if (!trend.length) {
    return (
      <div style={{
        height: 220,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "var(--text-muted)",
        fontSize: 13,
      }}>
        Not enough date data to show trend
      </div>
    );
  }

  const formatted = trend.map((d) => ({
    ...d,
    date: (() => {
      try { return format(parseISO(d.date), "MMM d"); }
      catch { return d.date; }
    })(),
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={formatted} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="gradPos" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#22c77c" stopOpacity={0.22} />
            <stop offset="95%" stopColor="#22c77c" stopOpacity={0}    />
          </linearGradient>
          <linearGradient id="gradNeg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#f0364f" stopOpacity={0.22} />
            <stop offset="95%" stopColor="#f0364f" stopOpacity={0}    />
          </linearGradient>
          <linearGradient id="gradNeu" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#e09e28" stopOpacity={0.18} />
            <stop offset="95%" stopColor="#e09e28" stopOpacity={0}    />
          </linearGradient>
        </defs>

        <CartesianGrid stroke="var(--chart-grid)" vertical={false} />

        <XAxis
          dataKey="date"
          tick={{ fill: "var(--chart-text)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: "var(--chart-text)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />

        <Tooltip content={<CustomTooltip />} />

        <Legend
          iconType="circle"
          iconSize={7}
          formatter={(v) => (
            <span style={{ color: "var(--chart-subtext)", fontSize: 11, textTransform: "capitalize" }}>{v}</span>
          )}
        />

        <Area type="monotone" dataKey="positive" stroke="#22c77c" strokeWidth={2} fill="url(#gradPos)" dot={false} />
        <Area type="monotone" dataKey="negative" stroke="#f0364f" strokeWidth={2} fill="url(#gradNeg)" dot={false} />
        <Area type="monotone" dataKey="neutral"  stroke="#e09e28" strokeWidth={2} fill="url(#gradNeu)" dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
