"""BeliefCollapseDetector -- Real-time relational collapse early warning.

Integrates signals from ToMTracker + LinguisticAlignmentScorer to compute
real-time collapse risk. The "canary" of the system.

Belief Collapse = the phase transition where Cost-of-Coordination (CoC)
exceeds Value-of-Connection (VOC). It is abrupt, not gradual.

Five signal channels, weighted:
    - epistemic_divergence (0.30)
    - linguistic_withdrawal (0.20)
    - defensive_attribution (0.25) -- LLM-detected blaming/projection
    - narrative_incoherence (0.15) -- shared story degrading
    - response_latency_proxy (0.10) -- shorter, terser responses
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from apriori.core.alignment_scorer import LinguisticAlignmentScorer
from apriori.core.tom_tracker import ToMTracker
from apriori.models.events import CrisisEpisode
from apriori.models.shadow_vector import SHADOW_VALUE_KEYS, BeliefState, ShadowVector

# ---------------------------------------------------------------------------
# LLM prompts
# ---------------------------------------------------------------------------

_DEFENSIVE_ATTRIBUTION_PROMPT = """\
Score the level of defensive attribution in the following conversation turns on a 0.0-1.0 scale.

Defensive attribution = ascribing negative motives to a partner without stated evidence.
Markers: "you always", "you never", "you just want to", "typical of you", blame-shifting,
assuming the worst interpretation of ambiguous behavior.

Turns:
{turns}

Be precise:
- 0.0-0.2 = healthy disagreement, no blame
- 0.3-0.5 = mild frustration, some uncharitable interpretations
- 0.6-0.7 = active blame, negative motive attribution
- 0.8-1.0 = sustained hostile attribution, contempt markers

Respond with ONLY a JSON object: {{"score": <float>, "evidence": "<1 sentence>"}}
"""

_NARRATIVE_INCOHERENCE_PROMPT = """\
Analyze the following conversation for narrative coherence of the shared relationship story.

Look for:
1. "We/us/our" statements (relationship identity)
2. Future-oriented statements ("we should", "next time we", "when we")
3. Past-only references without future framing
4. Contradictions in how they describe their relationship

Turns:
{turns}

Score narrative incoherence 0.0-1.0:
- 0.0 = strong shared narrative, future-oriented, "we" language
- 0.5 = mixed signals, some shared framing but cracks visible
- 1.0 = no shared narrative, past-only, contradictory accounts

Respond with ONLY a JSON object: {{"score": <float>, "has_future_statements": <bool>, "evidence": "<1 sentence>"}}
"""


class BeliefCollapseDetector:
    """Integrates signals from ToMTracker + LinguisticAlignmentScorer to compute
    real-time collapse risk. The "canary" of the system.

    Belief Collapse = the phase transition where Cost-of-Coordination exceeds
    Value-of-Connection. It's abrupt, not gradual.

    Parameters
    ----------
    tom_tracker_a:
        ToMTracker instance for agent A.
    tom_tracker_b:
        ToMTracker instance for agent B.
    linguistic_scorer:
        LinguisticAlignmentScorer tracking both agents.
    llm_client:
        LangChain chat model for defensive attribution / narrative analysis.
    history_window:
        Number of recent turns to consider for signal computation.
    """

    COLLAPSE_SIGNALS: Dict[str, float] = {
        "epistemic_divergence": 0.30,
        "linguistic_withdrawal": 0.20,
        "defensive_attribution": 0.25,
        "narrative_incoherence": 0.15,
        "response_latency_proxy": 0.10,
    }

    def __init__(
        self,
        tom_tracker_a: ToMTracker,
        tom_tracker_b: ToMTracker,
        linguistic_scorer: LinguisticAlignmentScorer,
        llm_client: Any,
        history_window: int = 15,
    ) -> None:
        self._tom_a = tom_tracker_a
        self._tom_b = tom_tracker_b
        self._linguistic = linguistic_scorer
        self._llm = llm_client
        self._history_window = history_window

        self._collapse_history: List[Dict[str, Any]] = []
        self._assessment_count: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def assess(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Full collapse risk assessment at the current moment.

        Returns
        -------
        dict
            overall_collapse_risk: float (0.0-1.0 composite score)
            risk_level: str
            signal_breakdown: Dict[str, float]
            primary_driver: str
            turns_until_likely_collapse: Optional[int]
            intervention_recommended: bool
            intervention_type: Optional[str]
            coc_estimate: float
            voc_estimate: float
            is_post_traumatic_growth: bool
        """
        self._assessment_count += 1
        recent = conversation_history[-self._history_window:]

        # Compute each signal
        epistemic = self._compute_epistemic_signal()
        withdrawal = self._compute_withdrawal_signal()
        defensive = await self._detect_defensive_attribution(recent)
        incoherence = await self._assess_narrative_incoherence(recent)
        latency = self._response_length_proxy(conversation_history)

        signal_breakdown = {
            "epistemic_divergence": round(epistemic, 4),
            "linguistic_withdrawal": round(withdrawal, 4),
            "defensive_attribution": round(defensive, 4),
            "narrative_incoherence": round(incoherence, 4),
            "response_latency_proxy": round(latency, 4),
        }

        # Weighted composite
        overall = sum(
            signal_breakdown[sig] * weight
            for sig, weight in self.COLLAPSE_SIGNALS.items()
        )
        overall = max(0.0, min(1.0, overall))

        risk_level = self._classify_risk_level(overall)
        primary_driver = max(signal_breakdown, key=signal_breakdown.get)  # type: ignore[arg-type]
        turns_until = self._project_turns_until_collapse(overall)

        intervention_needed = risk_level in ("CRITICAL", "HIGH")
        intervention_type = (
            self.suggest_intervention({"primary_driver": primary_driver, "risk_level": risk_level})
            if intervention_needed
            else None
        )

        coc = self._estimate_coc(signal_breakdown)
        voc = self._estimate_voc(signal_breakdown)
        ptg = self._detect_post_traumatic_growth()

        result = {
            "overall_collapse_risk": round(overall, 4),
            "risk_level": risk_level,
            "signal_breakdown": signal_breakdown,
            "primary_driver": primary_driver,
            "turns_until_likely_collapse": turns_until,
            "intervention_recommended": intervention_needed,
            "intervention_type": intervention_type,
            "coc_estimate": round(coc, 4),
            "voc_estimate": round(voc, 4),
            "is_post_traumatic_growth": ptg,
        }

        self._collapse_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "assessment": result,
        })

        return result

    def compute_coc_voc(
        self,
        shadow_a: ShadowVector,
        shadow_b: ShadowVector,
        episode_history: List[CrisisEpisode],
    ) -> Tuple[float, float]:
        """Compute Cost-of-Coordination and Value-of-Connection.

        CoC(A,B,t) = alpha * divergence + beta * epistemic_mismatch + gamma * unresolved_crisis_load
        VOC(A,B,t) = exponentially-weighted sum of narrative coherence over past episodes

        alpha=0.40, beta=0.35, gamma=0.25, lambda(decay)=0.1

        Returns
        -------
        tuple[float, float]
            (coc, voc). If coc > voc: imminent collapse.
        """
        alpha, beta, gamma = 0.40, 0.35, 0.25
        decay_lambda = 0.1

        div_a = self._avg_divergence(self._tom_a)
        div_b = self._avg_divergence(self._tom_b)
        divergence = (div_a + div_b) / 2.0

        mismatch = self._epistemic_mismatch(shadow_a, shadow_b)

        if episode_history:
            unresolved = sum(1 for ep in episode_history if not ep.reached_homeostasis)
            crisis_load = unresolved / len(episode_history)
        else:
            crisis_load = 0.0

        coc = alpha * divergence + beta * mismatch + gamma * crisis_load

        if episode_history:
            voc = 0.0
            total_weight = 0.0
            for i, ep in enumerate(reversed(episode_history)):
                weight = math.exp(-decay_lambda * i)
                voc += weight * ep.narrative_elasticity_score
                total_weight += weight
            voc = voc / total_weight if total_weight > 0 else 0.0
        else:
            voc = 0.5

        return (round(coc, 4), round(voc, 4))

    def suggest_intervention(self, risk_assessment: Dict) -> str:
        """Rules-based intervention selector.

        - epistemic_divergence primary + CRITICAL -> ``"reanchor"`` (shared history prompt)
        - defensive_attribution primary -> ``"deescalate"`` (inject neutral reframing)
        - linguistic_withdrawal + HIGH -> ``"validate"`` (explicit acknowledgment prompt)
        - narrative_incoherence primary -> ``"reframe"`` (future-orientation injection)

        Returns
        -------
        str
            Intervention type.
        """
        driver = risk_assessment.get("primary_driver", "")
        level = risk_assessment.get("risk_level", "LOW")

        if driver == "epistemic_divergence" and level == "CRITICAL":
            return "reanchor"
        if driver == "defensive_attribution":
            return "deescalate"
        if driver == "linguistic_withdrawal" and level in ("HIGH", "CRITICAL"):
            return "validate"
        if driver == "narrative_incoherence":
            return "reframe"

        if level == "CRITICAL":
            return "deescalate"
        if level == "HIGH":
            return "validate"
        return "reframe"

    def get_collapse_history(self) -> List[Dict]:
        """Return all recorded collapse assessments with timestamps and recovery outcomes."""
        return list(self._collapse_history)

    # ------------------------------------------------------------------
    # Signal computation
    # ------------------------------------------------------------------

    def _compute_epistemic_signal(self) -> float:
        """Average epistemic divergence across both trackers, normalized to [0, 1].

        JSD is bounded by ln(2) ~ 0.693, so we normalize by that.
        """
        div_a = self._avg_divergence(self._tom_a)
        div_b = self._avg_divergence(self._tom_b)
        raw = (div_a + div_b) / 2.0
        return min(1.0, raw / 0.693)

    def _compute_withdrawal_signal(self) -> float:
        """Linguistic withdrawal signal: 1.0 if both agents, 0.5 if one, 0.0 if neither."""
        a_wd = self._linguistic.detect_withdrawal_signal(self._tom_a.agent_id)
        b_wd = self._linguistic.detect_withdrawal_signal(self._tom_b.agent_id)

        if a_wd and b_wd:
            return 1.0
        if a_wd or b_wd:
            return 0.5
        return 0.0

    async def _detect_defensive_attribution(
        self,
        conversation_history: List[Dict],
        window: int = 5,
    ) -> float:
        """Use LLM to detect defensive attribution in the last N turns.

        Defensive attribution: ascribing negative motives to partner without evidence.

        Returns
        -------
        float
            Score in [0.0, 1.0].
        """
        recent = conversation_history[-window:]
        if not recent:
            return 0.0

        turns_str = "\n".join(
            f"[{t.get('agent', t.get('role', '?'))}]: {t.get('content', t.get('text', ''))}"
            for t in recent
        )

        prompt = _DEFENSIVE_ATTRIBUTION_PROMPT.format(turns=turns_str)
        raw = await self._llm_json_call(prompt)
        return max(0.0, min(1.0, float(raw.get("score", 0.0))))

    async def _assess_narrative_incoherence(
        self,
        conversation_history: List[Dict],
    ) -> float:
        """Assess degradation of the shared relationship narrative.

        Checks for we/us/our statements, future-orientation, and contradictions.

        Returns
        -------
        float
            Incoherence score in [0.0, 1.0].
        """
        if not conversation_history:
            return 0.0

        turns_str = "\n".join(
            f"[{t.get('agent', t.get('role', '?'))}]: {t.get('content', t.get('text', ''))}"
            for t in conversation_history
        )

        prompt = _NARRATIVE_INCOHERENCE_PROMPT.format(turns=turns_str)
        raw = await self._llm_json_call(prompt)
        return max(0.0, min(1.0, float(raw.get("score", 0.0))))

    def _response_length_proxy(self, conversation_history: List[Dict]) -> float:
        """Compare avg response length: last 5 turns vs prior 10.

        Ratio < 0.5 -> terse withdrawal signal. Normalized to [0.0, 1.0].
        """
        if len(conversation_history) < 15:
            return 0.0

        recent_5 = conversation_history[-5:]
        prior_10 = conversation_history[-15:-5]

        def avg_len(turns: List[Dict]) -> float:
            lengths = [len(t.get("content", t.get("text", ""))) for t in turns]
            return sum(lengths) / max(len(lengths), 1)

        recent_avg = avg_len(recent_5)
        prior_avg = avg_len(prior_10)

        if prior_avg == 0:
            return 0.0

        ratio = recent_avg / prior_avg
        if ratio >= 1.0:
            return 0.0
        if ratio <= 0.2:
            return 1.0
        return (1.0 - ratio) / 0.8

    # ------------------------------------------------------------------
    # CoC / VoC helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _avg_divergence(tracker: ToMTracker) -> float:
        """Average epistemic divergence across all models in a tracker."""
        state = tracker.get_belief_state()
        models = state.epistemic_models
        if not models:
            return 0.0
        return sum(m.epistemic_divergence for m in models.values()) / len(models)

    def _epistemic_mismatch(self, shadow_a: ShadowVector, shadow_b: ShadowVector) -> float:
        """How differently A and B see each other vs reality. Normalized to [0, 1]."""
        state_a = self._tom_a.get_belief_state()
        state_b = self._tom_b.get_belief_state()

        model_a_about_b = state_a.epistemic_models.get(self._tom_b.agent_id)
        model_b_about_a = state_b.epistemic_models.get(self._tom_a.agent_id)

        if not model_a_about_b or not model_b_about_a:
            return 0.5

        a_errors = [
            abs(model_a_about_b.l1_belief.values[k] - shadow_b.values[k])
            for k in SHADOW_VALUE_KEYS
        ]
        b_errors = [
            abs(model_b_about_a.l1_belief.values[k] - shadow_a.values[k])
            for k in SHADOW_VALUE_KEYS
        ]

        avg_error = (sum(a_errors) + sum(b_errors)) / (2 * len(SHADOW_VALUE_KEYS))
        return min(1.0, avg_error)

    @staticmethod
    def _estimate_coc(signal_breakdown: Dict[str, float]) -> float:
        """Estimate Cost of Coordination from current signal values."""
        return (
            0.40 * signal_breakdown.get("epistemic_divergence", 0.0)
            + 0.35 * signal_breakdown.get("defensive_attribution", 0.0)
            + 0.25 * signal_breakdown.get("response_latency_proxy", 0.0)
        )

    @staticmethod
    def _estimate_voc(signal_breakdown: Dict[str, float]) -> float:
        """Estimate Value of Connection (inverse of incoherence + withdrawal)."""
        incoherence = signal_breakdown.get("narrative_incoherence", 0.0)
        withdrawal = signal_breakdown.get("linguistic_withdrawal", 0.0)
        return max(0.0, 1.0 - 0.6 * incoherence - 0.4 * withdrawal)

    # ------------------------------------------------------------------
    # Projections & detection
    # ------------------------------------------------------------------

    def _project_turns_until_collapse(self, current_risk: float) -> Optional[int]:
        """Project turns until likely collapse based on risk velocity.

        Uses last 5 assessments to compute average risk change per turn.
        Returns None if stable or improving.
        """
        if len(self._collapse_history) < 3:
            return None

        recent_risks = [
            h["assessment"]["overall_collapse_risk"]
            for h in self._collapse_history[-5:]
        ]

        if len(recent_risks) < 2:
            return None

        deltas = [recent_risks[i + 1] - recent_risks[i] for i in range(len(recent_risks) - 1)]
        velocity = sum(deltas) / len(deltas)

        if velocity <= 0.01:
            return None

        remaining = 1.0 - current_risk
        return max(1, int(remaining / velocity))

    def _detect_post_traumatic_growth(self) -> bool:
        """Check for post-traumatic growth: risk peaked earlier and has since recovered.

        Requires >= 5 assessments, a peak > 0.5, and current risk < 60% of peak.
        """
        if len(self._collapse_history) < 5:
            return False

        risks = [h["assessment"]["overall_collapse_risk"] for h in self._collapse_history]
        peak = max(risks)
        peak_idx = risks.index(peak)
        current = risks[-1]

        return peak_idx < len(risks) - 2 and peak > 0.5 and current < peak * 0.6

    # ------------------------------------------------------------------
    # Risk classification
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_risk_level(score: float) -> str:
        """Map composite collapse risk to a human-readable level.

        - CRITICAL: > 0.80
        - HIGH: > 0.60
        - MODERATE: > 0.40
        - LOW: > 0.20
        - STABLE: <= 0.20
        """
        if score > 0.80:
            return "CRITICAL"
        if score > 0.60:
            return "HIGH"
        if score > 0.40:
            return "MODERATE"
        if score > 0.20:
            return "LOW"
        return "STABLE"

    # ------------------------------------------------------------------
    # LLM helper
    # ------------------------------------------------------------------

    async def _llm_json_call(self, prompt: str) -> Dict[str, Any]:
        """Invoke the LLM and parse the response as JSON."""
        response = await self._llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [line for line in lines if not line.strip().startswith("```")]
            content = "\n".join(lines).strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"score": 0.0, "evidence": "Failed to parse LLM response"}

    def __repr__(self) -> str:
        return (
            f"BeliefCollapseDetector("
            f"agents=[{self._tom_a.agent_id!r}, {self._tom_b.agent_id!r}], "
            f"assessments={self._assessment_count}, "
            f"history_window={self._history_window})"
        )
