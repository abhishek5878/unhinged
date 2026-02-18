import type {
  MatchCandidate,
  PastSimulation,
  SimulationResults,
  Timeline,
} from "@/types/simulation";

export const mockCandidates: MatchCandidate[] = [
  {
    user_id: "mock-001",
    first_name: "Priya",
    city: "Mumbai",
    attachment_style: "anxious",
    shared_vulnerability_hint:
      "You both highly value achievement. Worth stress-testing.",
  },
  {
    user_id: "mock-002",
    first_name: "Rohan",
    city: "Bangalore",
    attachment_style: "secure",
    shared_vulnerability_hint:
      "Shared fear of engulfment — could create distance under pressure.",
  },
  {
    user_id: "mock-003",
    first_name: "Ananya",
    city: "Delhi",
    attachment_style: "avoidant",
    shared_vulnerability_hint:
      "Opposing communication styles — direct vs. indirect. High signal.",
  },
];

export const mockPastSimulations: PastSimulation[] = [
  {
    simulation_id: "sim-001",
    partner_name: "Priya",
    date: "2026-02-15",
    homeostasis_rate: 0.73,
    primary_risk: "Financial Stress",
    status: "completed",
  },
  {
    simulation_id: "sim-002",
    partner_name: "Kavya",
    date: "2026-02-12",
    homeostasis_rate: 0.45,
    primary_risk: "Intimacy Withdrawal",
    status: "completed",
  },
  {
    simulation_id: "sim-003",
    partner_name: "Rohan",
    date: "2026-02-10",
    homeostasis_rate: 0.81,
    primary_risk: "Career Disruption",
    status: "completed",
  },
  {
    simulation_id: "sim-004",
    partner_name: "Ananya",
    date: "2026-02-18",
    homeostasis_rate: 0,
    primary_risk: "—",
    status: "running",
  },
];

// Generate a mock timeline for report demo
function mockTimeline(index: number): Timeline {
  const axes = [
    "intimacy",
    "autonomy",
    "security",
    "achievement",
    "belonging",
  ];
  const severity = 0.1 + (index / 100) * 0.85;
  const survived = Math.random() > severity * 0.7;
  const resilience = survived ? 0.4 + Math.random() * 0.5 : Math.random() * 0.3;

  return {
    timeline_id: `tl-${String(index).padStart(3, "0")}`,
    seed: index,
    pair_id: "mock-pair",
    crisis_severity: parseFloat(severity.toFixed(2)),
    crisis_axis: axes[index % axes.length],
    reached_homeostasis: survived,
    narrative_elasticity: parseFloat(
      (survived ? 0.5 + Math.random() * 0.4 : Math.random() * 0.4).toFixed(2)
    ),
    final_resilience_score: parseFloat(resilience.toFixed(2)),
    antifragile: resilience > 0.6,
    turns_total: 25 + Math.floor(Math.random() * 15),
    belief_collapse_events: survived ? 0 : 1 + Math.floor(Math.random() * 3),
    linguistic_convergence_final: parseFloat(
      (0.3 + Math.random() * 0.6).toFixed(2)
    ),
    full_transcript: [
      {
        role: "agent_a",
        content:
          "I've been thinking about what you said yesterday. About needing space.",
        timestamp: "2026-02-15T10:00:00Z",
      },
      {
        role: "agent_b",
        content:
          "I didn't mean it the way it sounded. I just needed time to process.",
        timestamp: "2026-02-15T10:01:00Z",
      },
      {
        role: "agent_a",
        content:
          "I know. It's just — when you go quiet, my mind fills in the worst versions.",
        timestamp: "2026-02-15T10:02:00Z",
      },
      {
        role: "agent_b",
        content:
          "That's fair. I should tell you when I'm stepping back, not just disappear.",
        timestamp: "2026-02-15T10:03:00Z",
      },
    ],
    belief_state_snapshots: [
      {
        turn: 5,
        risk: 0.15,
        risk_level: "LOW",
        signal_breakdown: {
          epistemic_divergence: 0.12,
          linguistic_withdrawal: 0.08,
          defensive_attribution: 0.05,
          narrative_incoherence: 0.1,
          response_latency_proxy: 0.03,
        },
      },
      {
        turn: 10,
        risk: 0.32,
        risk_level: "LOW",
        signal_breakdown: {
          epistemic_divergence: 0.25,
          linguistic_withdrawal: 0.15,
          defensive_attribution: 0.12,
          narrative_incoherence: 0.18,
          response_latency_proxy: 0.08,
        },
      },
      {
        turn: 15,
        risk: survived ? 0.55 : 0.72,
        risk_level: survived ? "MODERATE" : "HIGH",
        signal_breakdown: {
          epistemic_divergence: 0.43,
          linguistic_withdrawal: 0.35,
          defensive_attribution: survived ? 0.22 : 0.48,
          narrative_incoherence: 0.3,
          response_latency_proxy: 0.15,
        },
      },
      {
        turn: 20,
        risk: survived ? 0.35 : 0.85,
        risk_level: survived ? "LOW" : "CRITICAL",
        signal_breakdown: {
          epistemic_divergence: survived ? 0.28 : 0.6,
          linguistic_withdrawal: survived ? 0.2 : 0.55,
          defensive_attribution: survived ? 0.15 : 0.58,
          narrative_incoherence: survived ? 0.22 : 0.52,
          response_latency_proxy: survived ? 0.1 : 0.4,
        },
      },
    ],
  };
}

export function generateMockResults(): SimulationResults {
  const timelines = Array.from({ length: 100 }, (_, i) => mockTimeline(i));
  const survived = timelines.filter((t) => t.reached_homeostasis);
  const antifragile = timelines.filter((t) => t.antifragile);

  return {
    pair_id: "mock-pair",
    n_simulations: 100,
    computed_at: new Date().toISOString(),
    homeostasis_rate: parseFloat((survived.length / 100).toFixed(2)),
    antifragility_rate: parseFloat((antifragile.length / 100).toFixed(2)),
    median_elasticity: 0.68,
    collapse_attribution: {
      intimacy: 0.35,
      autonomy: 0.25,
      security: 0.2,
      achievement: 0.12,
      belonging: 0.08,
    },
    primary_collapse_vector: "intimacy",
    p20_homeostasis: 0.82,
    p80_homeostasis: 0.41,
    timelines,
  };
}
