"use client";

import Link from "next/link";
import { StatCard } from "./StatCard";
import { SurvivalCurve } from "./SurvivalCurve";
import { TimelineGrid } from "./TimelineGrid";
import { CrisisBreakdown } from "./CrisisBreakdown";
import { EpistemicGapViz } from "./EpistemicGapViz";
import { LinguisticConvergenceChart } from "./LinguisticConvergenceChart";
import type { SimulationResults } from "@/types/simulation";

interface SimulationReportProps {
  simulationId: string;
  results: SimulationResults;
  reportText: string;
  nameA?: string;
  nameB?: string;
}

function rateColor(rate: number): string {
  if (rate >= 0.7) return "#00ff9d";
  if (rate >= 0.5) return "#fbbf24";
  return "#ef4444";
}

export function SimulationReport({
  simulationId,
  results,
  reportText,
  nameA = "You",
  nameB = "Partner",
}: SimulationReportProps) {
  const collapsed = results.timelines.filter((t) => !t.reached_homeostasis);
  const topCollapseAxis = results.primary_collapse_vector;
  const collapsesByAxis = collapsed.filter(
    (t) => t.crisis_axis === topCollapseAxis
  ).length;

  function handleWhatsAppShare() {
    const origin = typeof window !== "undefined" ? window.location.origin : "https://prelude.app";
    const homeostasisPct = Math.round(results.homeostasis_rate * 100);
    const text = encodeURIComponent(
      `PRELUDE simulated ${results.n_simulations} futures of my relationship. ${homeostasisPct}% reached homeostasis. Top tension pattern: ${topCollapseAxis ?? "unknown"}. See yours: ${origin}/match`
    );
    window.open(`https://wa.me/?text=${text}`, "_blank");
  }

  return (
    <div className="mx-auto max-w-[820px] space-y-16 pb-20">
      {/* Section 1 — Header */}
      <section>
        <p className="font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-[0.3em] text-[#e8f4ff]/30">
          PRELUDE — Simulation Report
        </p>
        <p className="mt-1 font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/20">
          {simulationId} · {new Date(results.computed_at).toLocaleDateString("en-IN")}
        </p>
        <div className="mt-4 flex items-start justify-between gap-4">
          <div>
            <h1 className="font-[family-name:var(--font-syne)] text-3xl font-extrabold text-[#e8f4ff] md:text-4xl">
              {nameA} & {nameB}
            </h1>
            <p className="mt-1 font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/40">
              {results.n_simulations} timelines · {new Date(results.computed_at).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}
            </p>
          </div>
          <button
            onClick={handleWhatsAppShare}
            className="shrink-0 rounded-lg bg-[#25d366] px-4 py-2 font-[family-name:var(--font-space-mono)] text-xs font-bold text-white transition-all hover:bg-[#25d366]/90"
          >
            Share on WhatsApp
          </button>
        </div>
      </section>

      {/* Section 2 — Three Numbers */}
      <section>
        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard
            label="Homeostasis Rate"
            value={`${Math.round(results.homeostasis_rate * 100)}%`}
            subtitle={`of ${results.n_simulations} simulated timelines reached stable equilibrium`}
            color={rateColor(results.homeostasis_rate)}
          />
          <StatCard
            label="Antifragility"
            value={`${Math.round(results.antifragility_rate * 100)}%`}
            subtitle="of timelines — relationship got stronger post-crisis"
            color="#00c8ff"
          />
          <StatCard
            label="Primary Risk"
            value={topCollapseAxis.charAt(0).toUpperCase() + topCollapseAxis.slice(1)}
            subtitle={`drove the most collapses (${collapsesByAxis} of ${collapsed.length})`}
            color="#ff6b35"
          />
        </div>
      </section>

      {/* Section 3 — Verdict */}
      <section>
        <p className="mb-3 font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30">
          Simulation Verdict
        </p>
        <div className="rounded-xl border border-[#162638] bg-[#060d14]/30 p-8">
          <p className="font-[family-name:var(--font-crimson-pro)] text-lg leading-relaxed text-[#e8f4ff]/70">
            {reportText ||
              `${nameA} and ${nameB} show ${results.homeostasis_rate >= 0.7 ? "strong" : results.homeostasis_rate >= 0.5 ? "moderate" : "fragile"} alignment under calm conditions, but the relationship architecture reveals specific vulnerability points under crisis. The primary fracture line runs through ${topCollapseAxis} — where epistemic models diverge most sharply. ${results.antifragility_rate > 0.15 ? `Notably, ${Math.round(results.antifragility_rate * 100)}% of timelines showed antifragile properties, suggesting that when repair succeeds, it tends to strengthen the relational foundation.` : "Antifragile repair was rare, suggesting that recovery from crisis, when it happens, tends to restore baseline rather than exceed it."}`}
          </p>
        </div>
      </section>

      {/* Section 4 — Survival Curve */}
      <section>
        <SurvivalCurve timelines={results.timelines} />
      </section>

      {/* Section 5 — Timeline Grid */}
      <section>
        <TimelineGrid timelines={results.timelines} />
      </section>

      {/* Section 6 — Crisis Breakdown */}
      <section>
        <CrisisBreakdown
          timelines={results.timelines}
          collapseAttribution={results.collapse_attribution}
        />
      </section>

      {/* Section 7 — Epistemic Gap */}
      <section>
        <EpistemicGapViz
          p20={results.p20_homeostasis}
          p80={results.p80_homeostasis}
          primaryVector={results.primary_collapse_vector}
        />
      </section>

      {/* Section 8 — Linguistic Convergence */}
      <section>
        <LinguisticConvergenceChart timelines={results.timelines} />
      </section>

      {/* Section 9 — Recommendations */}
      <section>
        <p className="mb-4 font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30">
          What This Means In Practice
        </p>
        <div className="space-y-6">
          <div className="rounded-xl border border-[#162638] p-6">
            <p className="font-[family-name:var(--font-syne)] font-bold text-[#e8f4ff]">
              1. Agree on a {topCollapseAxis} protocol before you need one.
            </p>
            <p className="mt-2 font-[family-name:var(--font-crimson-pro)] text-sm text-[#e8f4ff]/50 leading-relaxed">
              Your simulations show that {topCollapseAxis}-related crises drive
              the most collapses. When this axis is stressed, epistemic
              divergence accelerates — you start misreading each other&apos;s
              responses. Decide now: what does your response protocol look like
              when {topCollapseAxis} pressure hits?
            </p>
          </div>
          <div className="rounded-xl border border-[#162638] p-6">
            <p className="font-[family-name:var(--font-syne)] font-bold text-[#e8f4ff]">
              2. Leverage your repair window.
            </p>
            <p className="mt-2 font-[family-name:var(--font-crimson-pro)] text-sm text-[#e8f4ff]/50 leading-relaxed">
              The simulations suggest a median elasticity of{" "}
              {(results.median_elasticity * 100).toFixed(0)}%. This means when
              crises hit, you have a meaningful window to repair before narrative
              collapse becomes irreversible. The key is to catch the
              divergence early — before defensive attribution takes over.
            </p>
          </div>
          <div className="rounded-xl border border-[#162638] p-6">
            <p className="font-[family-name:var(--font-syne)] font-bold text-[#e8f4ff]">
              3. Name the pattern, don&apos;t fight the person.
            </p>
            <p className="mt-2 font-[family-name:var(--font-crimson-pro)] text-sm text-[#e8f4ff]/50 leading-relaxed">
              Across {results.n_simulations} simulated timelines, the
              relationships that survived had one thing in common: they named
              the dynamic instead of blaming each other. &ldquo;We&apos;re in our
              avoidance-anxiety loop again&rdquo; lands differently than
              &ldquo;You always shut down.&rdquo;
            </p>
          </div>
        </div>
      </section>

      {/* Bottom actions */}
      <section className="flex flex-col gap-3 sm:flex-row">
        <Link
          href="/dashboard"
          className="flex-1 rounded-lg bg-[#00c8ff] px-6 py-3 text-center font-[family-name:var(--font-syne)] text-sm font-bold text-[#020408] transition-all hover:bg-[#00c8ff]/90"
        >
          Simulate with someone else
        </Link>
        <Link
          href="/dashboard/simulations"
          className="flex-1 rounded-lg border border-[#162638] px-6 py-3 text-center font-[family-name:var(--font-syne)] text-sm font-bold text-[#e8f4ff]/50 transition-all hover:border-[#e8f4ff]/20 hover:text-[#e8f4ff]/70"
        >
          View all simulations
        </Link>
      </section>
    </div>
  );
}
