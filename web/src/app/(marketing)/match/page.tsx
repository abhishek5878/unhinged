"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { joinWaitlist } from "@/lib/api";

// ---------------------------------------------------------------------------
// Section 1 — Hero
// ---------------------------------------------------------------------------

function HeroSection() {
  return (
    <section className="relative flex min-h-screen items-center justify-center overflow-hidden px-4">
      {/* Gradient mesh background */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% 40%, #00c8ff08 0%, transparent 70%), radial-gradient(ellipse 60% 50% at 30% 70%, #ff6b3506 0%, transparent 70%)",
        }}
      />

      {/* Orbital rings */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div className="absolute h-[600px] w-[600px] animate-[spin_30s_linear_infinite] rounded-full border border-[#00c8ff]/10" />
        <div className="absolute h-[450px] w-[450px] animate-[spin_20s_linear_infinite_reverse] rounded-full border border-[#ff6b35]/10" />
        <div className="absolute h-[300px] w-[300px] animate-[spin_15s_linear_infinite] rounded-full border border-[#00c8ff]/5" />
        {/* Orbiting dots */}
        <div className="absolute h-[600px] w-[600px] animate-[spin_30s_linear_infinite]">
          <div className="absolute left-1/2 top-0 h-2 w-2 -translate-x-1/2 rounded-full bg-[#00c8ff]/60" />
        </div>
        <div className="absolute h-[450px] w-[450px] animate-[spin_20s_linear_infinite_reverse]">
          <div className="absolute left-1/2 top-0 h-2 w-2 -translate-x-1/2 rounded-full bg-[#ff6b35]/60" />
        </div>
      </div>

      <div className="relative z-10 max-w-3xl text-center">
        <div className="mb-6 inline-block rounded-full border border-[#162638] bg-[#060d14]/80 px-4 py-1.5">
          <span className="font-[family-name:var(--font-space-mono)] text-[11px] uppercase tracking-[0.25em] text-[#00c8ff]/80">
            PRELUDE
          </span>
        </div>
        <h1 className="font-[family-name:var(--font-syne)] text-5xl font-extrabold leading-[1.1] tracking-tight text-[#e8f4ff] md:text-7xl">
          See the relationship
          <br />
          <span className="bg-gradient-to-r from-[#00c8ff] to-[#ff6b35] bg-clip-text text-transparent">
            before the relationship.
          </span>
        </h1>
        <p className="mx-auto mt-6 max-w-xl font-[family-name:var(--font-crimson-pro)] text-lg leading-relaxed text-[#e8f4ff]/60 md:text-xl">
          We simulate 100+ futures of your relationship — the fights, the
          growth, the breaking points — so you know what you&apos;re walking
          into.
        </p>
        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <a
            href="#waitlist"
            className="rounded-lg bg-[#00c8ff] px-8 py-4 font-[family-name:var(--font-syne)] text-sm font-bold text-[#020408] transition-all hover:bg-[#00c8ff]/90 hover:shadow-[0_0_30px_#00c8ff30]"
          >
            Get early access
          </a>
          <a
            href="#how-it-works"
            className="rounded-lg border border-[#162638] px-8 py-4 font-[family-name:var(--font-syne)] text-sm font-bold text-[#e8f4ff]/70 transition-all hover:border-[#00c8ff]/30 hover:text-[#e8f4ff]"
          >
            Watch it work
          </a>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 2 — The Problem
// ---------------------------------------------------------------------------

const problemCards = [
  {
    title: "Dating apps",
    desc: "Optimise for first dates. Swipe, match, ghost. Repeat.",
    color: "#e8f4ff",
  },
  {
    title: "PRELUDE",
    desc: "Simulates the relationship you\u2019d actually build \u2014 fights, growth, repair \u2014 across 100+ futures.",
    color: "#00c8ff",
    highlight: true,
  },
];

function ProblemSection() {
  return (
    <section className="px-4 py-24 md:py-32">
      <div className="mx-auto max-w-4xl">
        <p className="mb-3 font-[family-name:var(--font-space-mono)] text-xs uppercase tracking-[0.3em] text-[#ff6b35]/70">
          The problem
        </p>
        <h2 className="font-[family-name:var(--font-syne)] text-3xl font-bold text-[#e8f4ff] md:text-4xl">
          Compatibility isn&apos;t chemistry.
          <br />
          <span className="text-[#e8f4ff]/50">It&apos;s architecture.</span>
        </h2>
        <p className="mt-4 max-w-2xl font-[family-name:var(--font-crimson-pro)] text-lg text-[#e8f4ff]/50">
          Chemistry tells you who excites you. Architecture tells you who can
          hold the weight of an actual life together. We model the architecture.
        </p>

        <div className="mt-12 grid gap-6 md:grid-cols-2">
          {problemCards.map((card) => (
            <div
              key={card.title}
              className="rounded-xl border p-8 transition-all"
              style={{
                borderColor: card.highlight
                  ? `${card.color}30`
                  : "#162638",
                background: card.highlight
                  ? `${card.color}08`
                  : "transparent",
              }}
            >
              <h3
                className="font-[family-name:var(--font-syne)] text-lg font-bold"
                style={{ color: card.color }}
              >
                {card.title}
              </h3>
              <p className="mt-3 font-[family-name:var(--font-crimson-pro)] text-[#e8f4ff]/60 leading-relaxed">
                {card.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 3 — How It Works
// ---------------------------------------------------------------------------

const steps = [
  {
    number: "01",
    title: "Build your Shadow Vector",
    desc: "8 immersive questions map your attachment style, values, fears, and communication patterns into a high-dimensional psychological profile.",
    icon: (
      <svg
        className="h-8 w-8 text-[#00c8ff]"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1.5}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0"
        />
      </svg>
    ),
  },
  {
    number: "02",
    title: "Monte Carlo simulation",
    desc: "Our Relational Foundation Model runs 100+ timeline simulations \u2014 injecting realistic crises to see how you\u2019d navigate them together.",
    icon: (
      <svg
        className="h-8 w-8 text-[#ff6b35]"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1.5}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5"
        />
      </svg>
    ),
  },
  {
    number: "03",
    title: "Get your Compatibility Report",
    desc: "A detailed report showing survival probability, crisis resilience, emotional repair dynamics, and narrative convergence \u2014 not a percentage, a prognosis.",
    icon: (
      <svg
        className="h-8 w-8 text-[#00c8ff]"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1.5}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
        />
      </svg>
    ),
  },
];

function HowItWorksSection() {
  return (
    <section id="how-it-works" className="px-4 py-24 md:py-32">
      <div className="mx-auto max-w-4xl">
        <p className="mb-3 font-[family-name:var(--font-space-mono)] text-xs uppercase tracking-[0.3em] text-[#00c8ff]/70">
          How it works
        </p>
        <h2 className="font-[family-name:var(--font-syne)] text-3xl font-bold text-[#e8f4ff] md:text-4xl">
          Three steps to relationship clarity.
        </h2>

        <div className="mt-16 space-y-12">
          {steps.map((step) => (
            <div key={step.number} className="flex gap-6 md:gap-8">
              <div className="flex flex-col items-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-xl border border-[#162638] bg-[#020408]">
                  {step.icon}
                </div>
                {step.number !== "03" && (
                  <div className="mt-2 h-full w-px bg-gradient-to-b from-[#162638] to-transparent" />
                )}
              </div>
              <div className="pb-4">
                <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#00c8ff]/50">
                  Step {step.number}
                </span>
                <h3 className="mt-1 font-[family-name:var(--font-syne)] text-xl font-bold text-[#e8f4ff]">
                  {step.title}
                </h3>
                <p className="mt-2 max-w-lg font-[family-name:var(--font-crimson-pro)] text-[#e8f4ff]/50 leading-relaxed">
                  {step.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 4 — Sample Report Preview
// ---------------------------------------------------------------------------

const reportMetrics = [
  { label: "Survival probability", value: "73%", color: "#00c8ff" },
  { label: "Crisis resilience", value: "0.81", color: "#ff6b35" },
  { label: "Narrative convergence", value: "High", color: "#00c8ff" },
  { label: "Repair success rate", value: "68%", color: "#ff6b35" },
];

function ReportPreviewSection() {
  return (
    <section className="px-4 py-24 md:py-32">
      <div className="mx-auto max-w-4xl">
        <p className="mb-3 font-[family-name:var(--font-space-mono)] text-xs uppercase tracking-[0.3em] text-[#ff6b35]/70">
          The report
        </p>
        <h2 className="font-[family-name:var(--font-syne)] text-3xl font-bold text-[#e8f4ff] md:text-4xl">
          Not a percentage.
          <br />
          <span className="text-[#e8f4ff]/50">A prognosis.</span>
        </h2>

        <div className="relative mt-12 rounded-2xl border border-[#162638] bg-[#020408] p-8 md:p-12">
          <div className="mb-8 flex items-center gap-3">
            <div className="h-3 w-3 rounded-full bg-[#00c8ff]" />
            <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/40">
              PRELUDE — Compatibility Report (Sample)
            </span>
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            {reportMetrics.map((m) => (
              <div key={m.label} className="rounded-lg border border-[#162638] p-5">
                <p className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/40">
                  {m.label}
                </p>
                <p
                  className="mt-2 font-[family-name:var(--font-syne)] text-2xl font-bold"
                  style={{ color: m.color }}
                >
                  {m.value}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-8 space-y-3">
            <div className="h-3 w-full rounded bg-[#162638]" />
            <div className="h-3 w-4/5 rounded bg-[#162638]" />
            <div className="h-3 w-3/5 rounded bg-[#162638]" />
          </div>

          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-40 rounded-b-2xl bg-gradient-to-t from-[#020408] to-transparent" />
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 5 — Trust / Numbers
// ---------------------------------------------------------------------------

const trustStats = [
  {
    number: "100+",
    label: "Simulated timelines",
    desc: "per match",
  },
  {
    number: "8",
    label: "Crisis axes",
    desc: "tested per timeline",
  },
  {
    number: "L2",
    label: "Theory of Mind",
    desc: "recursive depth",
  },
];

function TrustSection() {
  return (
    <section className="px-4 py-24 md:py-32">
      <div className="mx-auto max-w-4xl">
        <p className="mb-3 font-[family-name:var(--font-space-mono)] text-xs uppercase tracking-[0.3em] text-[#e8f4ff]/20">
          Built on research
        </p>
        <div className="mt-8 grid gap-6 sm:grid-cols-3">
          {trustStats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl border border-[#162638] bg-[#060d14]/30 p-6 text-center"
            >
              <p className="font-[family-name:var(--font-syne)] text-3xl font-extrabold text-[#00c8ff]">
                {stat.number}
              </p>
              <p className="mt-2 font-[family-name:var(--font-space-mono)] text-xs uppercase tracking-wider text-[#e8f4ff]/50">
                {stat.label}
              </p>
              <p className="mt-1 font-[family-name:var(--font-crimson-pro)] text-sm text-[#e8f4ff]/30">
                {stat.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 6 — Waitlist CTA
// ---------------------------------------------------------------------------

const cities = [
  "Mumbai",
  "Delhi",
  "Bangalore",
  "Hyderabad",
  "Pune",
  "Chennai",
  "Kolkata",
  "Ahmedabad",
  "Jaipur",
  "Lucknow",
  "Other",
];

function WaitlistCTASection() {
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [city, setCity] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{
    position: number;
    referral_code: string;
    total_signups: number;
  } | null>(null);
  const [error, setError] = useState("");

  const ref = searchParams.get("ref") || undefined;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email || !city) return;

    setSubmitting(true);
    setError("");

    try {
      const data = await joinWaitlist({ email, city, ref, source: "match_page" });
      setResult({
        position: data.position,
        referral_code: data.referral_code,
        total_signups: data.total_signups,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section id="waitlist" className="px-4 py-24 md:py-32">
      <div className="mx-auto max-w-xl text-center">
        <p className="mb-3 font-[family-name:var(--font-space-mono)] text-xs uppercase tracking-[0.3em] text-[#00c8ff]/70">
          Early access
        </p>
        <h2 className="font-[family-name:var(--font-syne)] text-3xl font-bold text-[#e8f4ff] md:text-4xl">
          Your city. Your spot.
        </h2>
        <p className="mx-auto mt-4 max-w-md font-[family-name:var(--font-crimson-pro)] text-lg text-[#e8f4ff]/50">
          We&apos;re launching city by city. Join the waitlist and we&apos;ll
          tell you when your cluster is live.
        </p>

        {result ? (
          <div className="mt-10 rounded-xl border border-[#00c8ff]/30 bg-[#00c8ff]/5 p-8">
            <p className="font-[family-name:var(--font-syne)] text-4xl font-extrabold text-[#00c8ff]">
              #{result.position}
            </p>
            <p className="mt-2 font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff]/60">
              of {result.total_signups} on the waitlist
            </p>
            <p className="mt-6 font-[family-name:var(--font-crimson-pro)] text-[#e8f4ff]/50">
              Share your referral link to move up:
            </p>
            <Link
              href={`/match/waitlist?code=${result.referral_code}`}
              className="mt-2 inline-block font-[family-name:var(--font-space-mono)] text-sm text-[#00c8ff] underline"
            >
              See your referral dashboard →
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-10 space-y-4">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              className="w-full rounded-lg border border-[#162638] bg-transparent px-5 py-4 font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff] placeholder:text-[#e8f4ff]/30 focus:border-[#00c8ff]/50 focus:outline-none transition-colors"
            />
            <select
              value={city}
              onChange={(e) => setCity(e.target.value)}
              required
              className="w-full appearance-none rounded-lg border border-[#162638] bg-[#020408] px-5 py-4 font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff] focus:border-[#00c8ff]/50 focus:outline-none transition-colors"
            >
              <option value="" disabled>
                Select your city
              </option>
              {cities.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            {error && (
              <p className="font-[family-name:var(--font-space-mono)] text-sm text-red-400">
                {error}
              </p>
            )}
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-lg bg-[#00c8ff] px-8 py-4 font-[family-name:var(--font-syne)] text-sm font-bold text-[#020408] transition-all hover:bg-[#00c8ff]/90 hover:shadow-[0_0_30px_#00c8ff30] disabled:opacity-50"
            >
              {submitting ? "Joining..." : "Get early access"}
            </button>
          </form>
        )}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Section 7 — Footer
// ---------------------------------------------------------------------------

function FooterSection() {
  return (
    <footer className="border-t border-[#162638] px-4 py-12">
      <div className="mx-auto flex max-w-4xl flex-col items-center gap-4 text-center">
        <p className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff]/80">
          PRELUDE
        </p>
        <p className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/30">
          See the relationship before the relationship.
        </p>
        <div className="mt-4 flex gap-6">
          <Link
            href="/sign-in"
            className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/40 hover:text-[#e8f4ff]/70 transition-colors"
          >
            Sign in
          </Link>
          <Link
            href="/sign-up"
            className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/40 hover:text-[#e8f4ff]/70 transition-colors"
          >
            Sign up
          </Link>
        </div>
        <p className="mt-6 font-[family-name:var(--font-space-mono)] text-[10px] text-[#e8f4ff]/20">
          &copy; {new Date().getFullYear()} PRELUDE. All rights reserved.
        </p>
      </div>
    </footer>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function MatchPage() {
  return (
    <main className="min-h-screen bg-[#020408]">
      <HeroSection />
      <ProblemSection />
      <HowItWorksSection />
      <ReportPreviewSection />
      <TrustSection />
      <Suspense fallback={null}>
        <WaitlistCTASection />
      </Suspense>
      <FooterSection />
    </main>
  );
}
