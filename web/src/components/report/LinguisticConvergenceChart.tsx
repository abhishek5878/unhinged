"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { Timeline } from "@/types/simulation";

interface LinguisticConvergenceChartProps {
  timelines: Timeline[];
}

export function LinguisticConvergenceChart({
  timelines,
}: LinguisticConvergenceChartProps) {
  // Sample 20 evenly spaced timelines for the chart
  const step = Math.max(1, Math.floor(timelines.length / 20));
  const data = timelines
    .filter((_, i) => i % step === 0)
    .slice(0, 20)
    .map((tl, i) => ({
      index: i + 1,
      convergence: parseFloat(
        (tl.linguistic_convergence_final * 100).toFixed(1)
      ),
    }));

  const avgConvergence =
    timelines.reduce((s, t) => s + t.linguistic_convergence_final, 0) /
    timelines.length;

  return (
    <div>
      <p className="mb-4 font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30">
        How Your Language Aligned
      </p>

      <div className="rounded-xl border border-[#162638] bg-[#060d14]/50 p-6">
        <p className="mb-4 font-[family-name:var(--font-crimson-pro)] text-sm text-[#e8f4ff]/50 leading-relaxed">
          Average linguistic convergence across all timelines:{" "}
          <strong className="text-[#00c8ff]">
            {(avgConvergence * 100).toFixed(0)}%
          </strong>
          .{" "}
          {avgConvergence > 0.6
            ? "Your communication patterns naturally aligned — shared phrases and framing developed organically across most timelines."
            : avgConvergence > 0.4
              ? "Moderate linguistic alignment. Your language adapted to each other in some timelines but remained distinct in others."
              : "Low linguistic convergence suggests fundamentally different communication frames that didn't merge under pressure."}
        </p>

        <div className="h-[120px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
              <XAxis dataKey="index" hide />
              <YAxis hide domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0a1520",
                  border: "1px solid #162638",
                  borderRadius: 8,
                  fontSize: 11,
                }}
                formatter={(value) => [
                  `${value}%`,
                  "Convergence",
                ]}
              />
              <Bar
                dataKey="convergence"
                fill="#00c8ff"
                radius={[2, 2, 0, 0]}
                opacity={0.7}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
