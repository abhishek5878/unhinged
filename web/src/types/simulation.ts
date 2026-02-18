export interface TranscriptEntry {
  role: "agent_a" | "agent_b";
  content: string;
  timestamp: string;
}

export interface BeliefSnapshot {
  turn: number;
  risk: number;
  risk_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  signal_breakdown: Record<string, number>;
}

export interface Timeline {
  timeline_id: string;
  seed: number;
  pair_id: string;
  crisis_severity: number;
  crisis_axis: string;
  reached_homeostasis: boolean;
  narrative_elasticity: number;
  final_resilience_score: number;
  antifragile: boolean;
  turns_total: number;
  belief_collapse_events: number;
  linguistic_convergence_final: number;
  full_transcript: TranscriptEntry[];
  belief_state_snapshots: BeliefSnapshot[];
}

export interface SimulationResults {
  pair_id: string;
  n_simulations: number;
  computed_at: string;
  homeostasis_rate: number;
  antifragility_rate: number;
  median_elasticity: number;
  collapse_attribution: Record<string, number>;
  primary_collapse_vector: string;
  p20_homeostasis: number;
  p80_homeostasis: number;
  timelines: Timeline[];
}

export interface SimulationStatus {
  simulation_id: string;
  pair_id: string;
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  n_timelines: number;
  temporal_workflow_id: string | null;
  results: SimulationResults | null;
  created_at: string;
  completed_at: string | null;
}

export interface SimulationProgress {
  completed: number;
  total: number;
  status: string;
  percent: number;
}

export interface MatchCandidate {
  user_id: string;
  first_name: string;
  city: string;
  attachment_style: "secure" | "anxious" | "avoidant" | "fearful";
  shared_vulnerability_hint: string;
}

export interface PastSimulation {
  simulation_id: string;
  partner_name: string;
  date: string;
  homeostasis_rate: number;
  primary_risk: string;
  status: "completed" | "running" | "failed";
}
