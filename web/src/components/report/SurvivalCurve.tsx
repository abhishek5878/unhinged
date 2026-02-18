"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { Timeline } from "@/types/simulation";

interface SurvivalCurveProps {
  timelines: Timeline[];
}

export function SurvivalCurve({ timelines }: SurvivalCurveProps) {
  // Bucket timelines by severity into 20 bins
  const bins = 20;
  const data = Array.from({ length: bins }, (_, i) => {
    const lo = i / bins;
    const hi = (i + 1) / bins;
    const bucket = timelines.filter(
      (t) => t.crisis_severity >= lo && t.crisis_severity < hi
    );
    const survived = bucket.filter((t) => t.reached_homeostasis).length;
    const rate = bucket.length > 0 ? survived / bucket.length : 1;

    return {
      severity: parseFloat(((lo + hi) / 2).toFixed(2)),
      homeostasis: parseFloat((rate * 100).toFixed(1)),
    };
  });

  // Find inflection point (where curve crosses 50%)
  const inflection = data.find((d) => d.homeostasis < 50);

  return (
    <div>
      <p className="mb-1 font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30">
        P(Homeostasis) vs Crisis Severity
      </p>
      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="survivalGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#00c8ff" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#00c8ff" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#162638" strokeDasharray="3 3" />
            <XAxis
              dataKey="severity"
              tick={{ fontSize: 10, fill: "#e8f4ff60" }}
              tickLine={false}
              axisLine={{ stroke: "#162638" }}
              label={{
                value: "Crisis Severity",
                position: "insideBottom",
                offset: -5,
                style: { fontSize: 10, fill: "#e8f4ff40" },
              }}
            />
            <YAxis
              tick={{ fontSize: 10, fill: "#e8f4ff60" }}
              tickLine={false}
              axisLine={{ stroke: "#162638" }}
              domain={[0, 100]}
              label={{
                value: "P(Homeostasis) %",
                angle: -90,
                position: "insideLeft",
                style: { fontSize: 10, fill: "#e8f4ff40" },
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0a1520",
                border: "1px solid #162638",
                borderRadius: 8,
                fontSize: 11,
              }}
              labelStyle={{ color: "#e8f4ff80" }}
              itemStyle={{ color: "#00c8ff" }}
              formatter={(value) => [`${value}%`, "Homeostasis"]}
              labelFormatter={(label) => `Severity: ${label}`}
            />
            {inflection && (
              <ReferenceLine
                x={inflection.severity}
                stroke="#ff6b35"
                strokeDasharray="5 5"
                strokeWidth={1}
              />
            )}
            <ReferenceLine
              y={50}
              stroke="#e8f4ff20"
              strokeDasharray="3 3"
            />
            <Area
              type="monotone"
              dataKey="homeostasis"
              stroke="#00c8ff"
              strokeWidth={2}
              fill="url(#survivalGrad)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      {inflection && (
        <p className="mt-2 font-[family-name:var(--font-crimson-pro)] text-xs text-[#ff6b35]/70">
          Relationship becomes fragile above severity {inflection.severity}
        </p>
      )}
    </div>
  );
}
