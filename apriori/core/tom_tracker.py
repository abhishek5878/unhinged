"""ToMTracker — Recursive Theory of Mind belief engine.

Maintains L0 (ShadowVector ground truth) through L3 (fourth-order meta-epistemic
loop) for a single agent across a conversation. Before EVERY utterance, call
``hidden_thought()`` to update the agent's belief state.

The core loop:
    1. Observe the other agent's utterance.
    2. Infer value signals via LLM (structured JSON output).
    3. Bayesian-update the L1 belief (what I think about them).
    4. Project the L2 belief (what I think they think about me).
    5. Optionally compute L3 (what I think they think I think about them).
    6. Compute epistemic divergence (Jensen-Shannon) as a collapse early-warning.
    7. Log everything to a hidden thought record never exposed in dialogue.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any, Dict, List

from apriori.models.shadow_vector import (
    SHADOW_VALUE_KEYS,
    AttachmentStyle,
    BeliefState,
    EpistemicModel,
    ShadowVector,
)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_INFER_VALUES_PROMPT = """\
You are a relational psychologist analyzing a single utterance for latent value signals.

Utterance: "{utterance}"

Rate the *implied importance shift* for each value dimension on a scale of -0.3 to +0.3 \
(delta from neutral). Most values should be near 0. Only values clearly signaled by the \
utterance should deviate.

Dimensions: autonomy, security, achievement, intimacy, novelty, stability, power, belonging.

Respond with ONLY a JSON object mapping each dimension to its float delta. Example:
{{"autonomy": 0.1, "security": -0.05, "achievement": 0.0, "intimacy": 0.2, \
"novelty": 0.0, "stability": -0.1, "power": 0.0, "belonging": 0.05}}
"""

_PROJECT_L2_PROMPT = """\
You are modeling what Agent {target} likely believes about Agent {owner}'s inner values, \
based ONLY on what {owner} has revealed in conversation so far.

Conversation history (most recent last):
{history}

Agent {owner}'s communication style: {comm_style}

For each value dimension, estimate what {target} probably infers about {owner}'s \
priorities on a 0.0-1.0 scale. This is NOT {owner}'s true self -- it is the *projected \
persona* {owner} has been performing.

Dimensions: autonomy, security, achievement, intimacy, novelty, stability, power, belonging.

Respond with ONLY a JSON object. Example:
{{"autonomy": 0.6, "security": 0.3, "achievement": 0.5, "intimacy": 0.4, \
"novelty": 0.7, "stability": 0.2, "power": 0.3, "belonging": 0.5}}
"""

_L3_PROMPT = """\
You are computing a fourth-order Theory of Mind projection.

Question: What does Agent {owner} believe that Agent {target} believes \
that {owner} believes about {target}'s values?

Context -- {owner}'s current L1 belief about {target}: {l1_json}
Context -- {owner}'s current L2 belief (what {target} thinks of {owner}): {l2_json}

For each value dimension, estimate the fourth-order projection on a 0.0-1.0 scale.

Dimensions: autonomy, security, achievement, intimacy, novelty, stability, power, belonging.

Respond with ONLY a JSON object.
"""

_VERBALIZE_PROMPT = """\
You are the inner voice of Agent {agent_id}. Verbalize your current epistemic state \
in first person, under 100 words.

Your TRUE values (L0 -- never revealed): {l0_json}
What you THINK about them (L1): {l1_json}
What you THINK they think about YOU (L2): {l2_json}
Epistemic divergence (KL): {divergence:.3f}
Collapse risk: {risk_level}

Write a brief inner monologue. Be honest and introspective. Note any gaps between \
who you really are and what you think they see. Mention if something feels risky.
"""

_STRATEGY_PROMPT = """\
Given the following epistemic state, recommend a single communication strategy \
in 1-2 sentences.

Agent: {agent_id}
Collapse risk: {risk_level}
Epistemic divergence: {divergence:.3f}
Primary gap: {primary_gap}
Attachment style: {attachment}

Strategies to choose from: validate, disclose, probe, deflect, reanchor, mirror.
Respond with ONLY a JSON object: {{"strategy": "<name>", "rationale": "<1 sentence>"}}
"""


class ToMTracker:
    """Maintains recursive Theory of Mind state for one agent.

    Before EVERY utterance, execute ``hidden_thought()`` to update belief state.

    Parameters
    ----------
    agent_id:
        Unique identifier for the agent this tracker belongs to.
    shadow:
        The agent's ground-truth latent state (L0). Never exposed in dialogue.
    llm_client:
        A LangChain chat model supporting ``ainvoke``. All calls use structured
        JSON output.
    recursion_depth:
        Maximum epistemic depth. 2 = L0-L2 (default). 3 = includes L3 loop.
    collapse_threshold:
        Epistemic divergence above which collapse risk becomes HIGH or CRITICAL.
    """

    def __init__(
        self,
        agent_id: str,
        shadow: ShadowVector,
        llm_client: Any,
        recursion_depth: int = 2,
        collapse_threshold: float = 0.65,
    ) -> None:
        if recursion_depth not in (2, 3):
            raise ValueError("recursion_depth must be 2 or 3")

        self.agent_id = agent_id
        self.shadow = shadow
        self._llm = llm_client
        self._recursion_depth = recursion_depth
        self._collapse_threshold = collapse_threshold

        self._belief_state = BeliefState(
            agent_id=agent_id,
            shadow=shadow,
        )
        self._thought_log: List[Dict[str, Any]] = []
        self._conversation_history: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def hidden_thought(
        self,
        other_id: str,
        last_utterance: str,
        conversation_history: List[Dict],
    ) -> Dict[str, Any]:
        """Execute a full epistemic update cycle.

        **Must** be called before every agent turn.

        Execution order
        ---------------
        1. Retrieve or initialize ``EpistemicModel`` for *other_id*.
        2. ``_infer_values_from_utterance`` -> L1 likelihood update.
        3. ``_bayesian_update`` -> new L1 posterior.
        4. ``_project_their_model_of_me`` -> L2 belief.
        5. If ``recursion_depth >= 3``: ``_compute_fourth_order_loop`` -> L3.
        6. ``_kl_divergence`` (L1.values, L2.values) -> epistemic divergence.
        7. Append to thought log.
        8. Return structured hidden-thought dict.

        Returns
        -------
        dict
            agent: str -- Agent identifier.
            timestamp: str -- ISO-8601 UTC timestamp.
            l1_update: Dict[str, float] -- Per-dimension value deltas applied to L1.
            l2_projection: Dict[str, float] -- Current L2 values after projection.
            epistemic_divergence: float -- Jensen-Shannon divergence between L1 and L2.
            collapse_risk: str -- "CRITICAL" | "HIGH" | "MODERATE" | "LOW".
            raw_thought: str -- Natural language inner monologue.
            recommended_strategy: str -- Communication strategy with rationale.
        """
        self._conversation_history = conversation_history
        self._belief_state.turn_number += 1

        # 1 -- Retrieve or initialize epistemic model
        model = self._get_or_init_model(other_id)

        # 2 -- Infer value signals from the last utterance
        likelihood = await self._infer_values_from_utterance(last_utterance)

        # 3 -- Bayesian update L1
        prior = dict(model.l1_belief.values)
        posterior = self._bayesian_update(prior, likelihood, model.belief_confidence)
        model.l1_belief.values = posterior
        l1_delta = {k: round(posterior[k] - prior[k], 4) for k in sorted(SHADOW_VALUE_KEYS)}

        # 4 -- L2 projection
        l2_values = await self._project_their_model_of_me(model)
        model.l2_belief.values = l2_values

        # 5 -- Optional L3
        if self._recursion_depth >= 3:
            model.l3_belief = await self._compute_fourth_order_loop(model)

        # 6 -- Epistemic divergence
        divergence = self._kl_divergence(model.l1_belief.values, model.l2_belief.values)
        model.epistemic_divergence = divergence

        # Confidence update: slow decay + small boost from low divergence
        model.belief_confidence = min(
            1.0,
            model.belief_confidence * 0.98 + (1.0 - min(divergence, 1.0)) * 0.03,
        )
        model.update_count += 1
        model.last_updated = datetime.now(timezone.utc)

        # Persist model back
        self._belief_state.epistemic_models[other_id] = model

        # Risk classification
        risk_level = self._classify_risk(divergence)

        # Verbalization + strategy
        raw_thought = await self._verbalize_internal_state(model)
        strategy = await self._recommend_strategy(model, risk_level)

        # 7 -- Build and store thought record
        thought_record: Dict[str, Any] = {
            "agent": self.agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "turn": self._belief_state.turn_number,
            "other_id": other_id,
            "l1_update": l1_delta,
            "l2_projection": dict(l2_values),
            "epistemic_divergence": round(divergence, 4),
            "collapse_risk": risk_level,
            "raw_thought": raw_thought,
            "recommended_strategy": strategy,
        }
        self._thought_log.append(thought_record)
        self._belief_state.hidden_thought_log.append(thought_record)

        return thought_record

    def get_belief_state(self) -> BeliefState:
        """Return the full current belief state snapshot."""
        return self._belief_state

    def get_epistemic_gap_report(self, other_id: str) -> Dict[str, Any]:
        """Full report: L0 vs L1 vs L2 divergences plus trend over last N turns.

        Returns
        -------
        dict
            Per-dimension absolute gaps between each layer pair, totals, the
            divergence trend, trend direction, confidence, and update count.
        """
        model = self._belief_state.epistemic_models.get(other_id)
        if model is None:
            return {"error": f"No epistemic model for {other_id}"}

        l0 = self.shadow.values
        l1 = model.l1_belief.values
        l2 = model.l2_belief.values

        l0_l1_gap = {k: round(abs(l0[k] - l1[k]), 4) for k in sorted(SHADOW_VALUE_KEYS)}
        l1_l2_gap = {k: round(abs(l1[k] - l2[k]), 4) for k in sorted(SHADOW_VALUE_KEYS)}
        l0_l2_gap = {k: round(abs(l0[k] - l2[k]), 4) for k in sorted(SHADOW_VALUE_KEYS)}

        relevant = [t for t in self._thought_log if t.get("other_id") == other_id]
        trend = [t["epistemic_divergence"] for t in relevant[-15:]]

        return {
            "other_id": other_id,
            "l0_vs_l1": l0_l1_gap,
            "l1_vs_l2": l1_l2_gap,
            "l0_vs_l2": l0_l2_gap,
            "l0_l1_total": round(sum(l0_l1_gap.values()), 4),
            "l1_l2_total": round(sum(l1_l2_gap.values()), 4),
            "l0_l2_total": round(sum(l0_l2_gap.values()), 4),
            "divergence_trend": trend,
            "trend_direction": self._trend_direction(trend),
            "current_confidence": model.belief_confidence,
            "update_count": model.update_count,
        }

    def get_thought_log(self, last_n: int = 10) -> List[Dict[str, Any]]:
        """Return the last *last_n* hidden thought records."""
        return self._thought_log[-last_n:]

    # ------------------------------------------------------------------
    # Core epistemic methods
    # ------------------------------------------------------------------

    async def _infer_values_from_utterance(self, utterance: str) -> Dict[str, float]:
        """Use the LLM to extract value-dimension deltas from a single utterance.

        Prompts the model to rate each of the 8 value dimensions on a [-0.3, +0.3]
        scale. Values clearly signaled by the utterance deviate from zero; everything
        else stays near 0.

        Returns
        -------
        dict
            Mapping of each value key to a clamped float delta.
        """
        prompt = _INFER_VALUES_PROMPT.format(utterance=utterance)
        raw = await self._llm_json_call(prompt)
        result: Dict[str, float] = {}
        for key in SHADOW_VALUE_KEYS:
            val = float(raw.get(key, 0.0))
            result[key] = max(-0.3, min(0.3, val))
        return result

    def _bayesian_update(
        self,
        prior: Dict[str, float],
        likelihood: Dict[str, float],
        confidence: float = 0.7,
    ) -> Dict[str, float]:
        """Weighted Bayesian update: ``posterior = prior + confidence * likelihood``.

        All outputs are clamped to [0.0, 1.0].

        Parameters
        ----------
        prior:
            Current belief values (0.0-1.0 per dimension).
        likelihood:
            Delta signals from utterance inference (roughly -0.3 to +0.3).
        confidence:
            How much to trust the new evidence (0.0-1.0).
        """
        posterior: Dict[str, float] = {}
        for key in SHADOW_VALUE_KEYS:
            p = prior.get(key, 0.5)
            l_delta = likelihood.get(key, 0.0)
            posterior[key] = max(0.0, min(1.0, p + confidence * l_delta))
        return posterior

    async def _project_their_model_of_me(self, model: EpistemicModel) -> Dict[str, float]:
        """L2 projection: what does the other agent think my values are?

        Uses conversation history to estimate which signals this agent has been
        sending about its own values -- the performed persona, crucially different
        from L0 (who the agent actually is).
        """
        history_str = self._format_history(self._conversation_history[-20:])
        prompt = _PROJECT_L2_PROMPT.format(
            target=model.target_agent_id,
            owner=self.agent_id,
            history=history_str,
            comm_style=self.shadow.communication_style,
        )
        raw = await self._llm_json_call(prompt)
        result: Dict[str, float] = {}
        for key in SHADOW_VALUE_KEYS:
            val = float(raw.get(key, 0.5))
            result[key] = max(0.0, min(1.0, val))
        return result

    async def _compute_fourth_order_loop(self, model: EpistemicModel) -> ShadowVector:
        """L3: What do I believe they believe I believe about them.

        Computationally expensive -- only triggered when ``recursion_depth >= 3``.
        Reuses the structural metadata (attachment, fears, etc.) from L1.
        """
        l1_json = json.dumps(dict(model.l1_belief.values))
        l2_json = json.dumps(dict(model.l2_belief.values))

        prompt = _L3_PROMPT.format(
            owner=self.agent_id,
            target=model.target_agent_id,
            l1_json=l1_json,
            l2_json=l2_json,
        )
        raw = await self._llm_json_call(prompt)
        values: Dict[str, float] = {}
        for key in SHADOW_VALUE_KEYS:
            val = float(raw.get(key, 0.5))
            values[key] = max(0.0, min(1.0, val))

        return ShadowVector(
            agent_id=model.target_agent_id,
            values=values,
            attachment_style=model.l1_belief.attachment_style,
            fear_architecture=list(model.l1_belief.fear_architecture),
            linguistic_signature=list(model.l1_belief.linguistic_signature),
            entropy_tolerance=model.l1_belief.entropy_tolerance,
            communication_style=model.l1_belief.communication_style,
        )

    def _kl_divergence(self, p: Dict[str, float], q: Dict[str, float]) -> float:
        """Symmetric KL divergence (Jensen-Shannon divergence) between two value dicts.

        Values are normalized to probability distributions before computing.
        Higher values indicate a larger epistemic gap between the self-model and
        the meta-projection.

        Returns
        -------
        float
            Non-negative JSD. Bounded above by ln(2) ~ 0.693.
        """
        p_dist = self._to_distribution(p)
        q_dist = self._to_distribution(q)
        m = [(pi + qi) / 2.0 for pi, qi in zip(p_dist, q_dist)]
        jsd = 0.5 * self._raw_kl(p_dist, m) + 0.5 * self._raw_kl(q_dist, m)
        return round(jsd, 6)

    # ------------------------------------------------------------------
    # Verbalization & strategy
    # ------------------------------------------------------------------

    async def _verbalize_internal_state(self, model: EpistemicModel) -> str:
        """Generate a first-person inner monologue of the current belief state.

        Produces a natural-language reflection (< 100 words) capturing the agent's
        awareness of epistemic gaps, risks, and relational dynamics. This text is
        part of the hidden thought log and is **never** exposed in dialogue.
        """
        risk = self._classify_risk(model.epistemic_divergence)
        prompt = _VERBALIZE_PROMPT.format(
            agent_id=self.agent_id,
            l0_json=json.dumps(dict(self.shadow.values)),
            l1_json=json.dumps(dict(model.l1_belief.values)),
            l2_json=json.dumps(dict(model.l2_belief.values)),
            divergence=model.epistemic_divergence,
            risk_level=risk,
        )
        response = await self._llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        return content.strip()

    async def _recommend_strategy(self, model: EpistemicModel, risk_level: str) -> str:
        """Use the LLM to recommend a communication strategy for the current state.

        Picks from: validate, disclose, probe, deflect, reanchor, mirror.
        Returns ``"<strategy>: <rationale>"``.
        """
        gaps = {
            k: abs(model.l1_belief.values[k] - model.l2_belief.values[k])
            for k in SHADOW_VALUE_KEYS
        }
        primary_gap = max(gaps, key=gaps.get)  # type: ignore[arg-type]

        prompt = _STRATEGY_PROMPT.format(
            agent_id=self.agent_id,
            risk_level=risk_level,
            divergence=model.epistemic_divergence,
            primary_gap=f"{primary_gap} (gap={gaps[primary_gap]:.2f})",
            attachment=self.shadow.attachment_style.value,
        )
        raw = await self._llm_json_call(prompt)
        strategy = raw.get("strategy", "probe")
        rationale = raw.get("rationale", "")
        return f"{strategy}: {rationale}"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_init_model(self, other_id: str) -> EpistemicModel:
        """Retrieve an existing EpistemicModel or create one with neutral priors.

        Neutral prior: all value dimensions at 0.5, SECURE attachment, empty fears,
        confidence at 0.3 (low -- we know almost nothing yet).
        """
        if other_id in self._belief_state.epistemic_models:
            return self._belief_state.epistemic_models[other_id]

        neutral_values = {k: 0.5 for k in SHADOW_VALUE_KEYS}

        l1_shadow = ShadowVector(
            agent_id=other_id,
            values=dict(neutral_values),
            attachment_style=AttachmentStyle.SECURE,
            fear_architecture=[],
            linguistic_signature=[],
            entropy_tolerance=0.5,
            communication_style="direct",
        )
        l2_shadow = ShadowVector(
            agent_id=self.agent_id,
            values=dict(neutral_values),
            attachment_style=self.shadow.attachment_style,
            fear_architecture=list(self.shadow.fear_architecture),
            linguistic_signature=list(self.shadow.linguistic_signature),
            entropy_tolerance=self.shadow.entropy_tolerance,
            communication_style=self.shadow.communication_style,
        )

        model = EpistemicModel(
            owner_agent_id=self.agent_id,
            target_agent_id=other_id,
            l1_belief=l1_shadow,
            l2_belief=l2_shadow,
            belief_confidence=0.3,
            epistemic_divergence=0.0,
        )
        self._belief_state.epistemic_models[other_id] = model
        return model

    def _classify_risk(self, divergence: float) -> str:
        """Map epistemic divergence to a collapse-risk category.

        - CRITICAL: divergence > 0.80
        - HIGH: divergence > collapse_threshold (default 0.65)
        - MODERATE: divergence > 0.40
        - LOW: divergence <= 0.40
        """
        if divergence > 0.80:
            return "CRITICAL"
        if divergence > self._collapse_threshold:
            return "HIGH"
        if divergence > 0.40:
            return "MODERATE"
        return "LOW"

    async def _llm_json_call(self, prompt: str) -> Dict[str, Any]:
        """Invoke the LLM and parse the response as JSON.

        Handles LangChain message objects and raw strings. Strips markdown
        code fences if present.
        """
        response = await self._llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [line for line in lines if not line.strip().startswith("```")]
            content = "\n".join(lines).strip()
        return json.loads(content)

    @staticmethod
    def _to_distribution(values: Dict[str, float]) -> List[float]:
        """Normalize a value dict into a probability distribution.

        Adds epsilon to avoid zeros, then normalizes so the vector sums to 1.
        Keys are sorted alphabetically for deterministic ordering.
        """
        epsilon = 1e-10
        raw = [max(values.get(k, 0.0), epsilon) for k in sorted(SHADOW_VALUE_KEYS)]
        total = sum(raw)
        return [v / total for v in raw]

    @staticmethod
    def _raw_kl(p: List[float], q: List[float]) -> float:
        """Compute KL(p || q) for two discrete distributions of equal length."""
        return sum(
            pi * math.log(pi / qi)
            for pi, qi in zip(p, q)
            if pi > 0 and qi > 0
        )

    @staticmethod
    def _format_history(history: List[Dict], max_entries: int = 20) -> str:
        """Format conversation history into a compact string for LLM prompts."""
        lines: List[str] = []
        for entry in history[-max_entries:]:
            speaker = entry.get("agent", entry.get("role", "unknown"))
            content = entry.get("content", entry.get("text", ""))
            lines.append(f"[{speaker}]: {content}")
        return "\n".join(lines) if lines else "(no history yet)"

    @staticmethod
    def _trend_direction(trend: List[float]) -> str:
        """Classify a divergence trend as increasing, decreasing, or stable.

        Compares the mean of the most recent 3 data points against the prior 3.
        A difference > 0.05 is increasing; < -0.05 is decreasing; else stable.
        """
        if len(trend) < 3:
            return "insufficient_data"
        recent = trend[-3:]
        earlier = trend[-6:-3] if len(trend) >= 6 else trend[:3]
        diff = (sum(recent) / len(recent)) - (sum(earlier) / len(earlier))
        if diff > 0.05:
            return "increasing"
        if diff < -0.05:
            return "decreasing"
        return "stable"

    def __repr__(self) -> str:
        divergences = {
            tid: round(m.epistemic_divergence, 3)
            for tid, m in self._belief_state.epistemic_models.items()
        }
        return (
            f"ToMTracker(agent={self.agent_id!r}, "
            f"depth=L{self._recursion_depth}, "
            f"turn={self._belief_state.turn_number}, "
            f"divergences={divergences})"
        )
