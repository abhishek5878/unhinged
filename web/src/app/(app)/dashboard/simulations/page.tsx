"use client";

import { useAuth } from "@clerk/nextjs";
import { PastSimulationsTable } from "@/components/dashboard/PastSimulationsTable";
import { mockPastSimulations } from "@/lib/mock-data";

export default function SimulationsPage() {
  const { isLoaded } = useAuth();

  if (!isLoaded) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-[#162638] border-t-[#00c8ff]" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8">
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

      <PastSimulationsTable simulations={mockPastSimulations} />
    </div>
  );
}
