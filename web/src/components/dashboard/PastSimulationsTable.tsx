"use client";

import Link from "next/link";
import type { PastSimulation } from "@/types/simulation";

const statusConfig: Record<
  string,
  { label: string; color: string; pulse: boolean }
> = {
  completed: { label: "Completed", color: "#00ff9d", pulse: false },
  running: { label: "Running", color: "#fbbf24", pulse: true },
  failed: { label: "Failed", color: "#ef4444", pulse: false },
};

function rateColor(rate: number): string {
  if (rate >= 0.7) return "#00ff9d";
  if (rate >= 0.5) return "#fbbf24";
  return "#ef4444";
}

interface PastSimulationsTableProps {
  simulations: PastSimulation[];
}

export function PastSimulationsTable({
  simulations,
}: PastSimulationsTableProps) {
  if (simulations.length === 0) {
    return (
      <p className="py-8 text-center font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff]/30">
        No simulations yet. Run your first one above.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-[#162638]">
            {["Partner", "Date", "Homeostasis", "Primary Risk", "Status"].map(
              (h) => (
                <th
                  key={h}
                  className="pb-3 text-left font-[family-name:var(--font-space-mono)] text-xs font-normal text-[#e8f4ff]/30"
                >
                  {h}
                </th>
              )
            )}
          </tr>
        </thead>
        <tbody>
          {simulations.map((sim) => {
            const st = statusConfig[sim.status] || statusConfig.completed;
            const href =
              sim.status === "completed"
                ? `/dashboard/simulation/${sim.simulation_id}/report`
                : `/dashboard/simulation/${sim.simulation_id}`;

            return (
              <tr
                key={sim.simulation_id}
                className="border-b border-[#162638]/50 transition-colors hover:bg-[#e8f4ff]/[0.02]"
              >
                <td className="py-4">
                  <Link
                    href={href}
                    className="font-[family-name:var(--font-syne)] text-sm font-medium text-[#e8f4ff] hover:text-[#00c8ff] transition-colors"
                  >
                    {sim.partner_name}
                  </Link>
                </td>
                <td className="py-4 font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/40">
                  {new Date(sim.date).toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "short",
                  })}
                </td>
                <td className="py-4">
                  {sim.status === "completed" ? (
                    <span
                      className="font-[family-name:var(--font-syne)] text-sm font-bold"
                      style={{ color: rateColor(sim.homeostasis_rate) }}
                    >
                      {Math.round(sim.homeostasis_rate * 100)}%
                    </span>
                  ) : (
                    <span className="text-[#e8f4ff]/20">—</span>
                  )}
                </td>
                <td className="py-4 font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/50">
                  {sim.primary_risk}
                </td>
                <td className="py-4">
                  <span className="inline-flex items-center gap-1.5">
                    <span
                      className={`h-2 w-2 rounded-full ${st.pulse ? "animate-pulse" : ""}`}
                      style={{ backgroundColor: st.color }}
                    />
                    <span
                      className="font-[family-name:var(--font-space-mono)] text-xs"
                      style={{ color: st.color }}
                    >
                      {st.label}
                    </span>
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
