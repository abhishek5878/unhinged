"use client";

import { useEffect, useState } from "react";
import { useAuth, useUser } from "@clerk/nextjs";
import { PastSimulationsTable } from "@/components/dashboard/PastSimulationsTable";
import { getMySimulations } from "@/lib/api";
import { mockPastSimulations } from "@/lib/mock-data";
import type { PastSimulation } from "@/types/simulation";

export default function SimulationsPage() {
  const { getToken } = useAuth();
  const { user } = useUser();
  const [sims, setSims] = useState<PastSimulation[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);

  const userId = (user?.publicMetadata as { user_id?: string })?.user_id;

  useEffect(() => {
    if (!userId) return;

    async function fetchSims() {
      setLoading(true);
      try {
        const token = await getToken();
        if (!token) throw new Error("No token");

        const data = await getMySimulations(token, userId!);
        if (data.length > 0) {
          setSims(
            data.map((s) => ({
              simulation_id: s.simulation_id,
              partner_name: "—",
              date: s.created_at,
              homeostasis_rate: s.homeostasis_rate ?? 0,
              primary_risk: s.primary_collapse_vector ?? "—",
              status: s.status as PastSimulation["status"],
            }))
          );
          setIsDemo(false);
        } else {
          setSims(mockPastSimulations);
          setIsDemo(true);
        }
      } catch {
        setSims(mockPastSimulations);
        setIsDemo(true);
      } finally {
        setLoading(false);
      }
    }

    fetchSims();
  }, [userId, getToken]);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-[#162638] border-t-[#00c8ff]" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      {isDemo && (
        <div className="rounded-lg border border-[#fbbf24]/30 bg-[#fbbf24]/5 px-4 py-3">
          <p className="font-[family-name:var(--font-space-mono)] text-xs text-[#fbbf24]">
            DEMO MODE — Showing sample data. Real simulations appear once you
            run your first one.
          </p>
        </div>
      )}

      <section>
        <p className="mb-1 font-[family-name:var(--font-space-mono)] text-xs uppercase tracking-[0.3em] text-[#00c8ff]/70">
          History
        </p>
        <h1 className="font-[family-name:var(--font-syne)] text-2xl font-bold text-[#e8f4ff]">
          All Simulations
        </h1>
        <p className="mt-1 font-[family-name:var(--font-crimson-pro)] text-sm text-[#e8f4ff]/40">
          Every timeline you&apos;ve explored.
        </p>
      </section>

      <PastSimulationsTable simulations={sims} />
    </div>
  );
}
