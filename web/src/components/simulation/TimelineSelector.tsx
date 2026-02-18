"use client";

import type { Timeline } from "@/types/simulation";

interface TimelineSelectorProps {
  timelines: Timeline[];
  selectedIndex: number;
  onSelect: (index: number) => void;
}

export function TimelineSelector({
  timelines,
  selectedIndex,
  onSelect,
}: TimelineSelectorProps) {
  const current = timelines[selectedIndex];

  return (
    <div className="flex items-center gap-3">
      <select
        value={selectedIndex}
        onChange={(e) => onSelect(Number(e.target.value))}
        className="appearance-none rounded-lg border border-[#162638] bg-[#060d14] px-3 py-2 font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff] focus:border-[#00c8ff]/50 focus:outline-none"
      >
        {timelines.map((tl, i) => (
          <option key={tl.timeline_id} value={i}>
            Timeline {i + 1} — {tl.reached_homeostasis ? "Survived" : "Collapsed"}{" "}
            (sev: {tl.crisis_severity.toFixed(2)})
          </option>
        ))}
      </select>
      {current && (
        <span
          className="rounded-full px-2 py-0.5 font-[family-name:var(--font-space-mono)] text-[10px]"
          style={{
            backgroundColor: current.reached_homeostasis
              ? "#00ff9d15"
              : "#ef444415",
            color: current.reached_homeostasis ? "#00ff9d" : "#ef4444",
          }}
        >
          {current.crisis_axis}
        </span>
      )}
    </div>
  );
}
