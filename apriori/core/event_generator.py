"""StochasticEventGenerator -- Precision chaos engine.

Targets the weakest link in the shared latent space between two agents.
Does NOT inject random events -- injects maximally destabilizing events
by analyzing shadow vectors for shared vulnerability axes.

The pipeline:
    1. Identify shared vulnerability via Hadamard product + fear intersection.
    2. Apply attachment-style resonance amplifiers.
    3. Sample severity from a configurable distribution (Pareto/uniform/beta).
    4. Generate a realistic crisis narrative via LLM.
    5. Predict collapse vectors and compute elasticity thresholds.
"""

from __future__ import annotations

import json
import math
import random
from typing import Any, Dict, List, Optional, Tuple

from apriori.models.events import BlackSwanEvent, EventTaxonomy
from apriori.models.shadow_vector import SHADOW_VALUE_KEYS, AttachmentStyle, ShadowVector

# ---------------------------------------------------------------------------
# Axis -> EventTaxonomy mapping
# ---------------------------------------------------------------------------

_AXIS_TO_EVENT: Dict[str, EventTaxonomy] = {
    "autonomy": EventTaxonomy.CAREER_DISRUPTION,
    "security": EventTaxonomy.FINANCIAL_COLLAPSE,
    "achievement": EventTaxonomy.CAREER_DISRUPTION,
    "intimacy": EventTaxonomy.BETRAYAL,
    "novelty": EventTaxonomy.VALUES_CONFLICT,
    "stability": EventTaxonomy.FINANCIAL_COLLAPSE,
    "power": EventTaxonomy.EXTERNAL_THREAT,
    "belonging": EventTaxonomy.LOSS,
}

# Fear -> axis mapping for the 1.4x shared-fear boost
_FEAR_TO_AXIS: Dict[str, str] = {
    "abandonment": "belonging",
    "failure": "achievement",
    "engulfment": "autonomy",
    "rejection": "intimacy",
    "loss": "security",
    "inadequacy": "achievement",
    "betrayal": "intimacy",
    "instability": "stability",
    "powerlessness": "power",
    "isolation": "belonging",
    "irrelevance": "power",
    "vulnerability": "security",
}

# ---------------------------------------------------------------------------
# LLM prompt
# ---------------------------------------------------------------------------

_NARRATIVE_PROMPT = """\
Generate a realistic crisis scenario. Parameters:
- Vulnerability axis being targeted: {axis}
- Both parties deeply value this (joint score: {score:.2f})
- Severity level: {severity:.2f}/1.0 (0=minor setback, 1=existential)
- Person A profile: {summary_a}
- Person B profile: {summary_b}

Output JSON with:
- narrative: 3 sentences describing what just happened (past tense, no resolution)
- decision_point: 1 sentence -- the immediate fork both parties face right now
- likely_a_reaction: predicted initial response type for A (1 sentence)
- likely_b_reaction: predicted initial response type for B (1 sentence)

Make it feel REAL. Not melodramatic. Real crises are mundane and devastating.\
"""


class StochasticEventGenerator:
    """Precision chaos engine. Targets the weakest link in the shared latent space.

    Does NOT inject random events -- injects maximally destabilizing events
    by analyzing both agents' shadow vectors for shared vulnerability.

    Parameters
    ----------
    llm_client:
        A LangChain chat model supporting ``ainvoke``.
    severity_distribution:
        Distribution for severity sampling: ``"pareto"`` | ``"uniform"`` | ``"beta"``.
    pareto_alpha:
        Shape parameter for Pareto distribution. Lower = heavier tail = more
        extreme events.
    """

    def __init__(
        self,
        llm_client: Any,
        severity_distribution: str = "pareto",
        pareto_alpha: float = 1.5,
    ) -> None:
        if severity_distribution not in ("pareto", "uniform", "beta"):
            raise ValueError(
                f"severity_distribution must be 'pareto', 'uniform', or 'beta', "
                f"got '{severity_distribution}'"
            )
        self._llm = llm_client
        self._severity_distribution = severity_distribution
        self._pareto_alpha = pareto_alpha

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def identify_shared_vulnerability(
        self,
        shadow_a: ShadowVector,
        shadow_b: ShadowVector,
    ) -> Tuple[str, float, str]:
        """Find the primary shared vulnerability axis between two agents.

        Algorithm
        ---------
        1. Compute Hadamard product of value dicts -> joint_stakes.
        2. Identify shared fears (set intersection of fear_architectures).
        3. Apply 1.4x boost to any value axis that maps to a shared fear.
        4. Check attachment style resonance and apply amplifiers:
           - Both anxious -> 1.3x on intimacy/belonging.
           - Both avoidant -> 1.3x on autonomy.
           - Anxious + Avoidant -> 1.6x on intimacy (highest amplification).
        5. Return (top_axis, score, 1-sentence explanation).

        Returns
        -------
        tuple[str, float, str]
            (vulnerability_axis, joint_severity_score, explanation)
        """
        # Step 1: Hadamard product
        joint_stakes: Dict[str, float] = {}
        for key in SHADOW_VALUE_KEYS:
            joint_stakes[key] = shadow_a.values[key] * shadow_b.values[key]

        # Step 2: Shared fears
        shared_fears = set(shadow_a.fear_architecture) & set(shadow_b.fear_architecture)

        # Step 3: 1.4x boost for axes mapped to shared fears
        for fear in shared_fears:
            axis = _FEAR_TO_AXIS.get(fear)
            if axis and axis in joint_stakes:
                joint_stakes[axis] *= 1.4

        # Step 4: Attachment style resonance
        styles = {shadow_a.attachment_style, shadow_b.attachment_style}
        if shadow_a.attachment_style == AttachmentStyle.ANXIOUS and shadow_b.attachment_style == AttachmentStyle.ANXIOUS:
            for axis in ("intimacy", "belonging"):
                if axis in joint_stakes:
                    joint_stakes[axis] *= 1.3
        elif shadow_a.attachment_style == AttachmentStyle.AVOIDANT and shadow_b.attachment_style == AttachmentStyle.AVOIDANT:
            if "autonomy" in joint_stakes:
                joint_stakes["autonomy"] *= 1.3
        elif {AttachmentStyle.ANXIOUS, AttachmentStyle.AVOIDANT} <= styles:
            # Anxious-avoidant trap: highest amplification on intimacy
            if "intimacy" in joint_stakes:
                joint_stakes["intimacy"] *= 1.6

        # Step 5: Find argmax
        top_axis = max(joint_stakes, key=joint_stakes.get)  # type: ignore[arg-type]
        score = joint_stakes[top_axis]

        fear_note = f" (shared fears: {', '.join(sorted(shared_fears))})" if shared_fears else ""
        explanation = (
            f"Both agents have high joint stakes in '{top_axis}' "
            f"(score={score:.3f}){fear_note}, making it the optimal destabilization target."
        )

        return top_axis, score, explanation

    async def generate_black_swan(
        self,
        shadow_a: ShadowVector,
        shadow_b: ShadowVector,
        severity_override: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> BlackSwanEvent:
        """Generate a maximally destabilizing Black Swan event.

        Full pipeline
        -------------
        1. ``identify_shared_vulnerability`` -> (axis, score, explanation).
        2. ``_sample_severity`` using configured distribution.
        3. ``_map_axis_to_event_type`` -> EventTaxonomy.
        4. ``_generate_narrative`` via LLM -> crisis scenario + decision point.
        5. ``_predict_collapse_vector`` -> expected shadow deltas per agent.
        6. ``_compute_elasticity_threshold`` -> minimum survival threshold.
        7. Assemble and return ``BlackSwanEvent``.

        Parameters
        ----------
        shadow_a, shadow_b:
            The two agents' ground-truth shadow vectors.
        severity_override:
            If provided, skips distribution sampling and uses this value directly.
        seed:
            Random seed for reproducibility.
        """
        if seed is not None:
            random.seed(seed)

        # 1 -- Identify vulnerability
        axis, vuln_score, _explanation = self.identify_shared_vulnerability(shadow_a, shadow_b)

        # 2 -- Sample severity
        severity = severity_override if severity_override is not None else self._sample_severity(vuln_score)

        # 3 -- Map to event type
        event_type = self._map_axis_to_event_type(axis)

        # 4 -- Generate narrative via LLM
        narrative_data = await self._generate_narrative(axis, vuln_score, severity, shadow_a, shadow_b)

        # 5 -- Predict collapse vector
        collapse_vector = self._predict_collapse_vector(shadow_a, shadow_b, axis, severity)

        # 6 -- Compute elasticity threshold
        threshold = self._compute_elasticity_threshold(shadow_a, shadow_b)

        return BlackSwanEvent(
            event_type=event_type,
            target_vulnerability_axis=axis,
            severity=round(severity, 4),
            narrative_description=narrative_data.get("narrative", "Crisis event occurred."),
            decision_point=narrative_data.get("decision_point", "Both parties must decide how to respond."),
            expected_collapse_vector=collapse_vector,
            elasticity_threshold=round(threshold, 4),
        )

    def measure_narrative_elasticity(
        self,
        pre_transcript: List[Dict],
        post_transcript: List[Dict],
        event: BlackSwanEvent,
        embedder: Any,
    ) -> float:
        """Measure how well the relational narrative survived a crisis.

        Embeds "relationship identity statements" (utterances containing we/us/our/
        together) from pre and post transcripts. If none found, uses last 5 turns
        as proxy.

        elasticity = cosine_similarity(pre_embedding, post_embedding)

        Values above ``event.elasticity_threshold`` indicate survival.

        Parameters
        ----------
        pre_transcript:
            Conversation turns before the crisis.
        post_transcript:
            Conversation turns after the crisis.
        event:
            The injected BlackSwanEvent (used for threshold comparison).
        embedder:
            A sentence-transformers model with an ``encode`` method.

        Returns
        -------
        float
            Elasticity score in [0.0, 1.0].
        """
        pre_identity = self._extract_identity_statements(pre_transcript)
        post_identity = self._extract_identity_statements(post_transcript)

        if not pre_identity:
            pre_identity = [
                t.get("content", t.get("text", ""))
                for t in pre_transcript[-5:]
            ]
        if not post_identity:
            post_identity = [
                t.get("content", t.get("text", ""))
                for t in post_transcript[-5:]
            ]

        if not pre_identity or not post_identity:
            return 0.0

        pre_emb = embedder.encode(" ".join(pre_identity))
        post_emb = embedder.encode(" ".join(post_identity))

        cosine_sim = self._cosine_similarity(list(pre_emb), list(post_emb))
        return max(0.0, min(1.0, cosine_sim))

    async def run_cascade(
        self,
        primary_event: BlackSwanEvent,
        shadow_a: ShadowVector,
        shadow_b: ShadowVector,
        n_aftershocks: int = 2,
    ) -> List[BlackSwanEvent]:
        """Generate a cascade of aftershock events following a primary crisis.

        Each aftershock has 60% of primary severity and may target different axes.
        Models the real phenomenon where one crisis weakens the system for the next.

        Returns
        -------
        list[BlackSwanEvent]
            List starting with the primary event followed by aftershocks.
        """
        cascade = [primary_event]
        aftershock_severity = primary_event.severity * 0.6

        for i in range(n_aftershocks):
            event = await self.generate_black_swan(
                shadow_a,
                shadow_b,
                severity_override=max(0.05, aftershock_severity * (0.8 ** i)),
            )
            cascade.append(event)

        return cascade

    # ------------------------------------------------------------------
    # Severity sampling
    # ------------------------------------------------------------------

    def _sample_severity(self, vulnerability_score: float) -> float:
        """Sample severity from the configured distribution, scaled by vulnerability.

        Pareto ensures most events are minor (0.1-0.3) with rare catastrophics (0.8+).
        The sample is multiplied by ``vulnerability_score`` to weight toward realistic
        severity. Final value is clamped to [0.05, 0.98].
        """
        if self._severity_distribution == "pareto":
            raw = (random.paretovariate(self._pareto_alpha) - 1.0) / 4.0
        elif self._severity_distribution == "uniform":
            raw = random.random()
        elif self._severity_distribution == "beta":
            raw = random.betavariate(2.0, 5.0)
        else:
            raw = random.random()

        scaled = raw * min(vulnerability_score, 1.5)
        return max(0.05, min(0.98, scaled))

    # ------------------------------------------------------------------
    # Event type mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _map_axis_to_event_type(axis: str) -> EventTaxonomy:
        """Map a vulnerability axis to the most relevant EventTaxonomy.

        Falls back to VALUES_CONFLICT for unmapped axes.
        """
        return _AXIS_TO_EVENT.get(axis, EventTaxonomy.VALUES_CONFLICT)

    # ------------------------------------------------------------------
    # Narrative generation (LLM)
    # ------------------------------------------------------------------

    async def _generate_narrative(
        self,
        axis: str,
        score: float,
        severity: float,
        shadow_a: ShadowVector,
        shadow_b: ShadowVector,
    ) -> Dict[str, str]:
        """Use the LLM to generate a realistic 3-sentence crisis scenario.

        Returns
        -------
        dict
            Keys: narrative, decision_point, likely_a_reaction, likely_b_reaction.
        """
        summary_a = self._summarize_shadow(shadow_a)
        summary_b = self._summarize_shadow(shadow_b)

        prompt = _NARRATIVE_PROMPT.format(
            axis=axis,
            score=score,
            severity=severity,
            summary_a=summary_a,
            summary_b=summary_b,
        )
        response = await self._llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        content = content.strip()

        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines).strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "narrative": content[:500],
                "decision_point": "Both parties must decide how to respond to this crisis.",
                "likely_a_reaction": "Unknown",
                "likely_b_reaction": "Unknown",
            }

    # ------------------------------------------------------------------
    # Collapse vector prediction
    # ------------------------------------------------------------------

    @staticmethod
    def _predict_collapse_vector(
        shadow_a: ShadowVector,
        shadow_b: ShadowVector,
        axis: str,
        severity: float,
    ) -> Dict[str, float]:
        """Predict the expected shadow-value delta for each agent.

        Higher severity and lower entropy_tolerance produce larger negative deltas
        on the targeted axis. Adjacent axes receive 30% spillover.

        Returns
        -------
        dict
            Keyed by agent_id with predicted total impact magnitude.
        """
        result: Dict[str, float] = {}
        for shadow in (shadow_a, shadow_b):
            primary = severity * (1.0 - shadow.entropy_tolerance) * shadow.values.get(axis, 0.5)
            secondary = primary * 0.3
            result[shadow.agent_id] = round(primary + secondary, 4)
        return result

    # ------------------------------------------------------------------
    # Elasticity threshold
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_elasticity_threshold(
        shadow_a: ShadowVector,
        shadow_b: ShadowVector,
    ) -> float:
        """Compute the minimum narrative elasticity score for this pair to survive.

        Formula: base(0.4) - 0.1 * avg_entropy_tolerance - 0.05 * attachment_bonus

        attachment_bonus: 2 if both SECURE, 1 if one SECURE, 0 otherwise.
        """
        avg_entropy = (shadow_a.entropy_tolerance + shadow_b.entropy_tolerance) / 2.0
        secure_count = sum(
            1 for s in (shadow_a, shadow_b)
            if s.attachment_style == AttachmentStyle.SECURE
        )
        threshold = 0.4 - 0.1 * avg_entropy - 0.05 * secure_count
        return max(0.05, min(0.95, threshold))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_identity_statements(transcript: List[Dict]) -> List[str]:
        """Extract utterances containing relationship identity markers (we/us/our/together)."""
        markers = {"we", "us", "our", "together"}
        results: List[str] = []
        for turn in transcript:
            text = turn.get("content", turn.get("text", ""))
            words = set(text.lower().split())
            if words & markers:
                results.append(text)
        return results

    @staticmethod
    def _summarize_shadow(shadow: ShadowVector) -> str:
        """Create a compact summary of a shadow vector for LLM prompts."""
        top_values = sorted(shadow.values.items(), key=lambda x: x[1], reverse=True)[:3]
        top_str = ", ".join(f"{k}={v:.2f}" for k, v in top_values)
        fears = ", ".join(shadow.fear_architecture[:3]) if shadow.fear_architecture else "none"
        return (
            f"[{shadow.attachment_style.value} attachment, "
            f"top values: {top_str}, "
            f"fears: {fears}, "
            f"entropy_tolerance: {shadow.entropy_tolerance:.2f}, "
            f"style: {shadow.communication_style}]"
        )

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def __repr__(self) -> str:
        return (
            f"StochasticEventGenerator("
            f"distribution={self._severity_distribution!r}, "
            f"alpha={self._pareto_alpha})"
        )
