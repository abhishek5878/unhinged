"use client";

interface EpistemicGapVizProps {
  p20: number;
  p80: number;
  primaryVector: string;
}

export function EpistemicGapViz({
  p20,
  p80,
  primaryVector,
}: EpistemicGapVizProps) {
  const gap = p20 - p80;
  const gapColor = gap > 0.3 ? "#ef4444" : gap > 0.15 ? "#fbbf24" : "#00ff9d";

  return (
    <div>
      <p className="mb-4 font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30">
        How Well You Understood Each Other
      </p>

      {/* Range visualization */}
      <div className="rounded-xl border border-[#162638] bg-[#060d14]/50 p-6">
        <div className="flex items-end justify-between">
          <div className="text-center">
            <p className="font-[family-name:var(--font-syne)] text-2xl font-bold text-[#00ff9d]">
              {Math.round(p20 * 100)}%
            </p>
            <p className="font-[family-name:var(--font-space-mono)] text-[9px] text-[#e8f4ff]/30">
              Low-stress homeostasis
            </p>
          </div>
          <div className="flex-1 px-4">
            <div className="relative h-3 rounded-full bg-[#162638]">
              <div
                className="absolute h-full rounded-full"
                style={{
                  left: `${(1 - p20) * 100}%`,
                  right: `${p80 * 100}%`,
                  backgroundColor: gapColor,
                  opacity: 0.4,
                }}
              />
              <div
                className="absolute top-1/2 h-4 w-4 -translate-y-1/2 rounded-full border-2 border-[#00ff9d] bg-[#060d14]"
                style={{ left: `${(1 - p20) * 100}%` }}
              />
              <div
                className="absolute top-1/2 h-4 w-4 -translate-y-1/2 rounded-full border-2 border-[#ef4444] bg-[#060d14]"
                style={{ left: `${(1 - p80) * 100}%` }}
              />
            </div>
            <p
              className="mt-2 text-center font-[family-name:var(--font-space-mono)] text-[10px]"
              style={{ color: gapColor }}
            >
              Gap: {(gap * 100).toFixed(0)} percentage points
            </p>
          </div>
          <div className="text-center">
            <p className="font-[family-name:var(--font-syne)] text-2xl font-bold text-[#ef4444]">
              {Math.round(p80 * 100)}%
            </p>
            <p className="font-[family-name:var(--font-space-mono)] text-[9px] text-[#e8f4ff]/30">
              High-stress homeostasis
            </p>
          </div>
        </div>

        <p className="mt-6 font-[family-name:var(--font-crimson-pro)] text-sm text-[#e8f4ff]/50 leading-relaxed">
          Under calm conditions, this pairing holds together{" "}
          <strong className="text-[#e8f4ff]/70">
            {Math.round(p20 * 100)}%
          </strong>{" "}
          of the time. But when crisis severity exceeds the 80th percentile, that
          drops to{" "}
          <strong className="text-[#e8f4ff]/70">
            {Math.round(p80 * 100)}%
          </strong>
          . The primary fracture point is{" "}
          <strong className="text-[#ff6b35]">
            {primaryVector.replace(/_/g, " ")}
          </strong>
          — this is where epistemic divergence accelerates fastest.
        </p>
      </div>
    </div>
  );
}
