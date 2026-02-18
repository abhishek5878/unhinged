"use client";

import { useState } from "react";
import type { Timeline } from "@/types/simulation";

type Filter = "all" | "survived" | "collapsed" | "antifragile";

interface TimelineGridProps {
  timelines: Timeline[];
}

function tileColor(tl: Timeline): string {
  if (tl.antifragile) return "#00c8ff";
  if (tl.reached_homeostasis) return "#00ff9d";
  return "#ef4444";
}

export function TimelineGrid({ timelines }: TimelineGridProps) {
  const [filter, setFilter] = useState<Filter>("all");

  const filtered = timelines.filter((tl) => {
    if (filter === "survived") return tl.reached_homeostasis;
    if (filter === "collapsed") return !tl.reached_homeostasis;
    if (filter === "antifragile") return tl.antifragile;
    return true;
  });

  const filters: { key: Filter; label: string }[] = [
    { key: "all", label: "All" },
    { key: "survived", label: "Survived" },
    { key: "collapsed", label: "Collapsed" },
    { key: "antifragile", label: "Antifragile" },
  ];

  return (
    <div>
      <p className="mb-3 font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30">
        {timelines.length} Simulation Timelines
      </p>

      {/* Filters */}
      <div className="mb-4 flex gap-2">
        {filters.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`rounded-md px-3 py-1.5 font-[family-name:var(--font-space-mono)] text-[10px] transition-all ${
              filter === f.key
                ? "bg-[#00c8ff]/10 text-[#00c8ff]"
                : "text-[#e8f4ff]/30 hover:text-[#e8f4ff]/50"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Grid */}
      <div className="flex flex-wrap gap-1">
        {timelines.map((tl, i) => {
          const visible = filtered.includes(tl);
          return (
            <div
              key={tl.timeline_id}
              className="group relative"
              style={{ opacity: visible ? 1 : 0.1 }}
            >
              <div
                className="h-[18px] w-[18px] rounded-[3px] transition-all hover:scale-125"
                style={{ backgroundColor: tileColor(tl) }}
              />
              {/* Tooltip */}
              <div className="pointer-events-none absolute -top-16 left-1/2 z-10 hidden -translate-x-1/2 rounded-lg border border-[#162638] bg-[#0a1520] px-3 py-2 group-hover:block">
                <p className="whitespace-nowrap font-[family-name:var(--font-space-mono)] text-[9px] text-[#e8f4ff]/60">
                  #{i + 1} · {tl.crisis_axis} · sev {tl.crisis_severity.toFixed(2)}
                </p>
                <p
                  className="font-[family-name:var(--font-space-mono)] text-[9px] font-medium"
                  style={{ color: tileColor(tl) }}
                >
                  {tl.antifragile
                    ? "Antifragile"
                    : tl.reached_homeostasis
                      ? "Survived"
                      : "Collapsed"}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-3 flex gap-4">
        {[
          { color: "#00ff9d", label: "Survived" },
          { color: "#ef4444", label: "Collapsed" },
          { color: "#00c8ff", label: "Antifragile" },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-1.5">
            <div
              className="h-2.5 w-2.5 rounded-[2px]"
              style={{ backgroundColor: item.color }}
            />
            <span className="font-[family-name:var(--font-space-mono)] text-[9px] text-[#e8f4ff]/40">
              {item.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
