import React from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { format, parseISO } from "date-fns";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "#17171f",
      border: "1px solid #2f2f3d",
      borderRadius: 10,
      padding: "12px 16px",
      fontSize: 13,
    }}>
      <p style={{ color: "#8a8699", marginBottom: 8, fontSize: 11 }}>
        {label}
      </p>
      {payload.map((p) => (
        <div key={p.dataKey} style={{ display: "flex", justifyContent: "space-between", gap: 16, marginBottom: 4 }}>
          <span style={{ color: p.color, textTransform: "capitalize" }}>{p.dataKey}</span>
          <span style={{ color: "#ede8d8", fontWeight: 600 }}>{p.value}</span>
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
        color: "#4e4b58",
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
            <stop offset="5%"  stopColor="#2dce89" stopOpacity={0.25} />
            <stop offset="95%" stopColor="#2dce89" stopOpacity={0}    />
          </linearGradient>
          <linearGradient id="gradNeg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#ff3d5a" stopOpacity={0.25} />
            <stop offset="95%" stopColor="#ff3d5a" stopOpacity={0}    />
          </linearGradient>
          <linearGradient id="gradNeu" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#f4a832" stopOpacity={0.20} />
            <stop offset="95%" stopColor="#f4a832" stopOpacity={0}    />
          </linearGradient>
        </defs>

        <CartesianGrid stroke="#1e1e28" vertical={false} />

        <XAxis
          dataKey="date"
          tick={{ fill: "#4e4b58", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: "#4e4b58", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />

        <Tooltip content={<CustomTooltip />} />

        <Legend
          iconType="circle"
          iconSize={7}
          formatter={(v) => (
            <span style={{ color: "#8a8699", fontSize: 11, textTransform: "capitalize" }}>{v}</span>
          )}
        />

        <Area type="monotone" dataKey="positive" stroke="#2dce89" strokeWidth={2} fill="url(#gradPos)" dot={false} />
        <Area type="monotone" dataKey="negative" stroke="#ff3d5a" strokeWidth={2} fill="url(#gradNeg)" dot={false} />
        <Area type="monotone" dataKey="neutral"  stroke="#f4a832" strokeWidth={2} fill="url(#gradNeu)" dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
