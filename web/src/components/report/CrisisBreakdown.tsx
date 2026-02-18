"use client";

import type { Timeline } from "@/types/simulation";

interface CrisisBreakdownProps {
  timelines: Timeline[];
  collapseAttribution: Record<string, number>;
}

const axisLabels: Record<string, string> = {
  intimacy: "Intimacy Withdrawal",
  autonomy: "Autonomy Conflict",
  security: "Financial Stress",
  achievement: "Career Disruption",
  belonging: "Social Isolation",
  novelty: "Stagnation Crisis",
  stability: "Upheaval Event",
  power: "Control Dynamics",
};

export function CrisisBreakdown({
  timelines,
  collapseAttribution,
}: CrisisBreakdownProps) {
  // Top 3 crisis axes by collapse attribution
  const topAxes = Object.entries(collapseAttribution)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

  return (
    <div>
      <p className="mb-4 font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30">
        What Broke You (And What Didn&apos;t)
      </p>

      <div className="grid gap-4 sm:grid-cols-3">
        {topAxes.map(([axis, attribution]) => {
          const axisTimelines = timelines.filter(
            (t) => t.crisis_axis === axis
          );
          const survived = axisTimelines.filter(
            (t) => t.reached_homeostasis
          ).length;
          const collapsed = axisTimelines.length - survived;
          const avgSeverity =
            axisTimelines.length > 0
              ? axisTimelines.reduce((s, t) => s + t.crisis_severity, 0) /
                axisTimelines.length
              : 0;
          const avgRecovery =
            survived > 0
              ? axisTimelines
                  .filter((t) => t.reached_homeostasis)
                  .reduce((s, t) => s + t.turns_total, 0) / survived
              : 0;

          const severityColor =
            avgSeverity > 0.7
              ? "#ef4444"
              : avgSeverity > 0.5
                ? "#f97316"
                : "#fbbf24";

          return (
            <div
              key={axis}
              className="rounded-xl border border-[#162638] p-5"
              style={{
                background: `linear-gradient(135deg, ${severityColor}05 0%, transparent 60%)`,
              }}
            >
              <h4 className="font-[family-name:var(--font-syne)] text-sm font-bold text-[#e8f4ff]">
                {axisLabels[axis] || axis}
              </h4>
              <span
                className="mt-1 inline-block rounded-full px-2 py-0.5 font-[family-name:var(--font-space-mono)] text-[9px]"
                style={{
                  backgroundColor: `${severityColor}15`,
                  color: severityColor,
                }}
              >
                SEVERITY {avgSeverity.toFixed(2)}
              </span>

              <p className="mt-3 font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/50">
                {axisTimelines.length} timelines tested — {survived} survived,{" "}
                {collapsed} collapsed
              </p>

              {survived > 0 && (
                <p className="mt-1 font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/30">
                  Average recovery: {avgRecovery.toFixed(1)} turns
                </p>
              )}

              {/* Attribution bar */}
              <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-[#162638]">
                <div
                  className="h-full rounded-full bg-[#ff6b35]"
                  style={{ width: `${attribution * 100}%` }}
                />
              </div>
              <p className="mt-1 font-[family-name:var(--font-space-mono)] text-[9px] text-[#e8f4ff]/30">
                {(attribution * 100).toFixed(0)}% of collapses
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
