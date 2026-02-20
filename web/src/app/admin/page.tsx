"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/backend";

interface WaitlistStats {
  total: number;
  conversions: number;
  cities: Record<string, number>;
  sources: Record<string, number>;
}

interface MetricCardProps {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}

function MetricCard({ label, value, sub, color }: MetricCardProps) {
  return (
    <div className="rounded-xl border border-[#162638] p-6">
      <p className="font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30">
        {label}
      </p>
      <p
        className="mt-3 font-[family-name:var(--font-syne)] text-3xl font-bold"
        style={{ color: color || "#e8f4ff" }}
      >
        {value}
      </p>
      {sub && (
        <p className="mt-1 font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/30">
          {sub}
        </p>
      )}
    </div>
  );
}

export default function AdminPage() {
  const { getToken } = useAuth();
  const [stats, setStats] = useState<WaitlistStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        const token = await getToken();
        if (!token) throw new Error("Not authenticated");

        const res = await fetch(`${BASE}/waitlist/stats`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setStats(await res.json());
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load stats");
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, [getToken]);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#162638] border-t-[#00c8ff]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-4xl">
        <div className="rounded-xl border border-[#ef4444]/30 bg-[#ef4444]/5 p-6">
          <p className="font-[family-name:var(--font-space-mono)] text-xs text-[#ef4444]">
            {error}
          </p>
        </div>
      </div>
    );
  }

  const conversionRate =
    stats && stats.total > 0
      ? ((stats.conversions / stats.total) * 100).toFixed(1)
      : "0.0";

  const topCities = stats
    ? Object.entries(stats.cities)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5)
    : [];

  const topSources = stats
    ? Object.entries(stats.sources)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5)
    : [];

  return (
    <div className="mx-auto max-w-5xl space-y-10">
      <section>
        <p className="mb-1 font-[family-name:var(--font-space-mono)] text-xs uppercase tracking-[0.3em] text-[#00c8ff]/70">
          Internal
        </p>
        <h1 className="font-[family-name:var(--font-syne)] text-2xl font-bold text-[#e8f4ff]">
          Admin Dashboard
        </h1>
        <p className="mt-1 font-[family-name:var(--font-crimson-pro)] text-sm text-[#e8f4ff]/40">
          Live metrics from the PRELUDE database.
        </p>
      </section>

      {/* Top metrics */}
      <div className="grid gap-4 sm:grid-cols-3">
        <MetricCard
          label="Waitlist signups"
          value={stats?.total ?? 0}
          color="#00c8ff"
        />
        <MetricCard
          label="Converted to users"
          value={stats?.conversions ?? 0}
          sub={`${conversionRate}% conversion`}
          color="#00ff9d"
        />
        <MetricCard
          label="Cities represented"
          value={Object.keys(stats?.cities ?? {}).length}
          color="#ff6b35"
        />
      </div>

      {/* City + Source breakdown */}
      <div className="grid gap-6 sm:grid-cols-2">
        {/* Cities */}
        <div className="rounded-xl border border-[#162638] p-6">
          <p className="font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30 mb-4">
            Top cities
          </p>
          {topCities.length === 0 ? (
            <p className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/20">
              No data yet
            </p>
          ) : (
            <div className="space-y-3">
              {topCities.map(([city, count]) => {
                const pct = stats
                  ? Math.round((count / stats.total) * 100)
                  : 0;
                return (
                  <div key={city}>
                    <div className="mb-1 flex justify-between">
                      <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/60">
                        {city || "Unknown"}
                      </span>
                      <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/40">
                        {count} · {pct}%
                      </span>
                    </div>
                    <div className="h-[3px] rounded-full bg-[#162638]">
                      <div
                        className="h-full rounded-full bg-[#00c8ff]"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Sources */}
        <div className="rounded-xl border border-[#162638] p-6">
          <p className="font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30 mb-4">
            Traffic sources
          </p>
          {topSources.length === 0 ? (
            <p className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/20">
              No data yet
            </p>
          ) : (
            <div className="space-y-3">
              {topSources.map(([source, count]) => {
                const pct = stats
                  ? Math.round((count / stats.total) * 100)
                  : 0;
                return (
                  <div key={source}>
                    <div className="mb-1 flex justify-between">
                      <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/60">
                        {source || "direct"}
                      </span>
                      <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/40">
                        {count} · {pct}%
                      </span>
                    </div>
                    <div className="h-[3px] rounded-full bg-[#162638]">
                      <div
                        className="h-full rounded-full bg-[#ff6b35]"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
