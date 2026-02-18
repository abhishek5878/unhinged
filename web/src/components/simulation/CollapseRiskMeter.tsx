"use client";

import { motion } from "framer-motion";

interface CollapseRiskMeterProps {
  risk: number; // 0-1
  riskLevel: string;
  signalBreakdown?: Record<string, number>;
}

function riskColor(risk: number): string {
  if (risk <= 0.4) return "#00ff9d";
  if (risk <= 0.65) return "#fbbf24";
  if (risk <= 0.8) return "#f97316";
  return "#ef4444";
}

export function CollapseRiskMeter({
  risk,
  riskLevel,
  signalBreakdown,
}: CollapseRiskMeterProps) {
  const color = riskColor(risk);
  const percent = Math.min(risk * 100, 100);

  return (
    <div className="p-3">
      <p className="mb-3 font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30">
        Collapse Risk
      </p>

      {/* Vertical gauge */}
      <div className="mx-auto flex w-16 flex-col items-center">
        <div className="relative h-[200px] w-6 overflow-hidden rounded-full bg-[#0a1520]">
          <motion.div
            className="absolute inset-x-0 bottom-0 rounded-full"
            style={{ backgroundColor: color }}
            initial={{ height: 0 }}
            animate={{ height: `${percent}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>
        <motion.p
          className="mt-3 font-[family-name:var(--font-syne)] text-2xl font-bold"
          style={{ color }}
          key={riskLevel}
          initial={{ scale: 1.2, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
        >
          {(risk * 100).toFixed(0)}%
        </motion.p>
        <p
          className="font-[family-name:var(--font-space-mono)] text-xs font-medium"
          style={{ color }}
        >
          {riskLevel}
        </p>
      </div>

      {/* Signal breakdown */}
      {signalBreakdown && (
        <div className="mt-6 space-y-2">
          {Object.entries(signalBreakdown).map(([signal, value]) => (
            <div key={signal}>
              <div className="flex items-center justify-between">
                <span className="font-[family-name:var(--font-space-mono)] text-[9px] text-[#e8f4ff]/40">
                  {signal.replace(/_/g, " ")}
                </span>
                <span className="font-[family-name:var(--font-space-mono)] text-[9px] text-[#e8f4ff]/50">
                  {value.toFixed(2)}
                </span>
              </div>
              <div className="mt-0.5 h-1 w-full overflow-hidden rounded-full bg-[#162638]">
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: riskColor(value) }}
                  initial={{ width: 0 }}
                  animate={{ width: `${value * 100}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
