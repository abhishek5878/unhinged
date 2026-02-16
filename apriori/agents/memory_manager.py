"""RelationshipMemoryManager -- Long-term episodic memory for agent pairs.

Uses Mem0 to give agents persistent memory across simulation episodes.
Enables agents to remember what happened "6 simulated months ago" and carry
learned beliefs and interaction patterns forward.

Memory taxonomy:
    - **EPISODIC**: Specific events/conversations ("the night of the startup failure").
    - **SEMANTIC**: Learned beliefs about the other ("they always get quiet when stressed").
    - **PROCEDURAL**: Learned interaction patterns ("apologizing works better than explaining").
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from apriori.models.events import CrisisEpisode
from apriori.models.shadow_vector import ShadowVector


class MemoryType(str, Enum):
    """Taxonomy of memory types stored in the relational memory system."""

    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class RelationshipMemoryManager:
    """Long-term episodic memory for agent pairs using Mem0.

    Enables agents to remember what happened "6 simulated months ago" by
    storing structured memories with type, emotional valence, and importance
    scoring. Memories are retrieved by semantic similarity to current context.

    Parameters
    ----------
    mem0_client:
        An initialized Mem0 ``MemoryClient`` instance (from ``mem0ai``).
    pair_id:
        Unique identifier for the agent pair this manager serves.
    """

    def __init__(self, mem0_client: Any, pair_id: str) -> None:
        self._client = mem0_client
        self._pair_id = pair_id
        self._memory_index: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def store_episode(
        self,
        episode: CrisisEpisode,
        shadow_a: ShadowVector,
        shadow_b: ShadowVector,
    ) -> str:
        """Extract and store memories from a completed crisis episode.

        After each crisis, extracts three categories of memory:
            1. **EPISODIC** -- What happened: a summary of the crisis and its outcome.
            2. **SEMANTIC** -- New beliefs formed about the other agent based on
               how they responded under stress.
            3. **PROCEDURAL** -- Which communication strategies worked or failed
               during the episode.

        Each memory is a structured dict with ``type``, ``content``, ``agents``,
        ``timestamp``, ``emotional_valence`` (-1 to 1), and ``importance_score``
        (0 to 1).

        Parameters
        ----------
        episode:
            The completed crisis episode with pre/post transcripts.
        shadow_a, shadow_b:
            Shadow vectors for context extraction.

        Returns
        -------
        str
            Memory ID for the stored episode bundle.
        """
        memory_id = str(uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        agents = [shadow_a.agent_id, shadow_b.agent_id]

        # Emotional valence: positive if homeostasis reached, negative if collapse
        valence = 0.4 if episode.reached_homeostasis else -0.6
        # Boost valence further if resilience was strong
        if episode.narrative_elasticity_score > 0.7:
            valence = min(1.0, valence + 0.3)

        # Importance: based on severity and whether it was resolved
        importance = min(1.0, episode.event.severity * 0.7 + 0.3)
        if not episode.reached_homeostasis:
            importance = min(1.0, importance + 0.2)

        # ----- 1. EPISODIC memory -----
        outcome = "reached homeostasis" if episode.reached_homeostasis else "ended in collapse"
        resolution_note = (
            f"Resolved in {episode.turns_to_resolution} turns."
            if episode.turns_to_resolution is not None
            else "Unresolved."
        )
        episodic_content = (
            f"Crisis: {episode.event.event_type.value} targeting {episode.event.target_vulnerability_axis}. "
            f"Severity: {episode.event.severity:.2f}. "
            f"{episode.event.narrative_description} "
            f"Outcome: {outcome}. {resolution_note} "
            f"Narrative elasticity: {episode.narrative_elasticity_score:.2f}."
        )

        episodic_memory = {
            "id": f"{memory_id}_episodic",
            "type": MemoryType.EPISODIC.value,
            "content": episodic_content,
            "agents": agents,
            "pair_id": self._pair_id,
            "timestamp": timestamp,
            "emotional_valence": round(valence, 2),
            "importance_score": round(importance, 2),
            "episode_id": episode.episode_id,
        }

        # ----- 2. SEMANTIC memories (one per agent) -----
        semantic_memories = []
        for shadow, transcript_key in [
            (shadow_a, "a_behavior"),
            (shadow_b, "b_behavior"),
        ]:
            behavior_summary = self._extract_behavior_pattern(
                shadow.agent_id,
                episode.post_crisis_transcript,
                episode.reached_homeostasis,
            )
            if behavior_summary:
                semantic_memories.append({
                    "id": f"{memory_id}_semantic_{shadow.agent_id}",
                    "type": MemoryType.SEMANTIC.value,
                    "content": behavior_summary,
                    "agents": agents,
                    "about_agent": shadow.agent_id,
                    "pair_id": self._pair_id,
                    "timestamp": timestamp,
                    "emotional_valence": round(valence, 2),
                    "importance_score": round(importance * 0.8, 2),
                    "episode_id": episode.episode_id,
                })

        # ----- 3. PROCEDURAL memory -----
        procedural_content = self._extract_procedural_knowledge(
            episode.post_crisis_transcript,
            episode.reached_homeostasis,
            episode.narrative_elasticity_score,
        )
        procedural_memory = {
            "id": f"{memory_id}_procedural",
            "type": MemoryType.PROCEDURAL.value,
            "content": procedural_content,
            "agents": agents,
            "pair_id": self._pair_id,
            "timestamp": timestamp,
            "emotional_valence": round(valence, 2),
            "importance_score": round(importance * 0.7, 2),
            "episode_id": episode.episode_id,
        }

        # Store all memories via Mem0
        all_memories = [episodic_memory] + semantic_memories + [procedural_memory]
        for mem in all_memories:
            self._client.add(
                messages=[{"role": "system", "content": mem["content"]}],
                user_id=self._pair_id,
                metadata={k: v for k, v in mem.items() if k != "content"},
            )
            self._memory_index.append(mem)

        return memory_id

    async def retrieve_relevant_memories(
        self,
        agent_id: str,
        current_context: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Retrieve memories relevant to the current conversation context.

        Uses Mem0's semantic search to find the most relevant stored memories,
        filtered to those involving the specified agent.

        Parameters
        ----------
        agent_id:
            Agent whose perspective to retrieve memories for.
        current_context:
            Current utterance or conversation snippet to match against.
        top_k:
            Maximum number of memories to return.

        Returns
        -------
        list[dict]
            Relevant memories sorted by relevance, each containing ``type``,
            ``content``, ``emotional_valence``, ``importance_score``, and
            ``timestamp``.
        """
        results = self._client.search(
            query=current_context,
            user_id=self._pair_id,
            limit=top_k * 2,  # over-fetch to allow filtering
        )

        # Normalize Mem0 response format
        memories = []
        raw_results = results if isinstance(results, list) else results.get("results", [])
        for item in raw_results:
            meta = item.get("metadata", {})
            agents = meta.get("agents", [])
            if agent_id in agents or not agents:
                memories.append({
                    "type": meta.get("type", "episodic"),
                    "content": item.get("memory", item.get("content", "")),
                    "emotional_valence": meta.get("emotional_valence", 0.0),
                    "importance_score": meta.get("importance_score", 0.5),
                    "timestamp": meta.get("timestamp", ""),
                    "about_agent": meta.get("about_agent", ""),
                })

        # Sort by importance and return top_k
        memories.sort(key=lambda m: m.get("importance_score", 0), reverse=True)
        return memories[:top_k]

    async def build_memory_context_string(
        self,
        agent_id: str,
        current_utterance: str,
    ) -> str:
        """Build a formatted string ready for injection into the agent system prompt.

        Retrieves relevant memories and formats them into a natural context block
        that the agent can draw on without explicitly referencing it.

        Format::

            Based on your shared history, you remember:
            - [3 months ago]: {episodic memory}
            - You've learned: {semantic belief}
            - You've found: {procedural knowledge}
            Keep this context in mind but don't reference it explicitly unless natural.

        Parameters
        ----------
        agent_id:
            Agent to build context for.
        current_utterance:
            Current conversation context for relevance matching.

        Returns
        -------
        str
            Formatted memory context string, or empty string if no memories exist.
        """
        memories = await self.retrieve_relevant_memories(
            agent_id, current_utterance, top_k=5
        )

        if not memories:
            return ""

        lines = ["Based on your shared history, you remember:"]
        for mem in memories:
            mem_type = mem.get("type", "episodic")
            content = mem.get("content", "")
            timestamp = mem.get("timestamp", "")

            if mem_type == MemoryType.EPISODIC.value:
                time_label = self._humanize_timestamp(timestamp)
                lines.append(f"- [{time_label}]: {content}")
            elif mem_type == MemoryType.SEMANTIC.value:
                lines.append(f"- You've learned: {content}")
            elif mem_type == MemoryType.PROCEDURAL.value:
                lines.append(f"- You've found: {content}")
            else:
                lines.append(f"- {content}")

        lines.append("Keep this context in mind but don't reference it explicitly unless natural.")
        return "\n".join(lines)

    async def compute_relationship_arc(self) -> Dict[str, Any]:
        """Analyze all stored memories to compute the relationship trajectory.

        Returns
        -------
        dict
            valence_trend: str
                ``"improving"`` | ``"declining"`` | ``"stable"``.
            avg_valence: float
                Mean emotional valence across all memories.
            key_turning_points: List[Dict]
                Episodes with the highest absolute valence.
            resilience_events: List[Dict]
                Episodes where homeostasis was reached despite high severity.
            total_episodes: int
                Total number of stored episode memories.
            predicted_trajectory: str
                ``"strengthening"`` | ``"weakening"`` | ``"plateau"``.
        """
        if not self._memory_index:
            return {
                "valence_trend": "stable",
                "avg_valence": 0.0,
                "key_turning_points": [],
                "resilience_events": [],
                "total_episodes": 0,
                "predicted_trajectory": "plateau",
            }

        episodic = [m for m in self._memory_index if m.get("type") == MemoryType.EPISODIC.value]

        if not episodic:
            return {
                "valence_trend": "stable",
                "avg_valence": 0.0,
                "key_turning_points": [],
                "resilience_events": [],
                "total_episodes": 0,
                "predicted_trajectory": "plateau",
            }

        valences = [m.get("emotional_valence", 0.0) for m in episodic]
        avg_valence = sum(valences) / len(valences)

        # Valence trend: compare first half to second half
        if len(valences) >= 4:
            mid = len(valences) // 2
            first_half = sum(valences[:mid]) / mid
            second_half = sum(valences[mid:]) / (len(valences) - mid)
            diff = second_half - first_half
            if diff > 0.15:
                valence_trend = "improving"
            elif diff < -0.15:
                valence_trend = "declining"
            else:
                valence_trend = "stable"
        else:
            valence_trend = "stable"

        # Key turning points: highest absolute valence
        sorted_by_abs = sorted(episodic, key=lambda m: abs(m.get("emotional_valence", 0.0)), reverse=True)
        turning_points = [
            {"content": m["content"], "valence": m["emotional_valence"], "timestamp": m.get("timestamp")}
            for m in sorted_by_abs[:3]
        ]

        # Resilience events: positive valence + high importance
        resilience = [
            {"content": m["content"], "valence": m["emotional_valence"], "importance": m.get("importance_score", 0)}
            for m in episodic
            if m.get("emotional_valence", 0) > 0.3 and m.get("importance_score", 0) > 0.6
        ]

        # Predicted trajectory
        if valence_trend == "improving" and avg_valence > 0:
            trajectory = "strengthening"
        elif valence_trend == "declining" and avg_valence < 0:
            trajectory = "weakening"
        else:
            trajectory = "plateau"

        return {
            "valence_trend": valence_trend,
            "avg_valence": round(avg_valence, 3),
            "key_turning_points": turning_points,
            "resilience_events": resilience,
            "total_episodes": len(episodic),
            "predicted_trajectory": trajectory,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_behavior_pattern(
        agent_id: str,
        post_crisis_transcript: List[Dict],
        reached_homeostasis: bool,
    ) -> str:
        """Extract a behavioral belief about an agent from their crisis response.

        Analyzes the post-crisis transcript to identify dominant communication
        patterns (withdrawal, engagement, deflection, etc.).
        """
        if not post_crisis_transcript:
            return ""

        agent_turns = [
            t.get("content", t.get("text", ""))
            for t in post_crisis_transcript
            if t.get("role", t.get("agent", "")) == agent_id
        ]

        if not agent_turns:
            return ""

        # Heuristic analysis of response patterns
        total_words = sum(len(t.split()) for t in agent_turns)
        avg_words = total_words / len(agent_turns) if agent_turns else 0

        # Check for emotional engagement markers
        emotional_markers = {"feel", "felt", "sorry", "understand", "hurt", "worried", "scared"}
        avoidance_markers = {"fine", "whatever", "okay", "sure", "anyway", "doesn't matter"}

        all_words_lower = set(" ".join(agent_turns).lower().split())
        emotional_count = len(emotional_markers & all_words_lower)
        avoidance_count = len(avoidance_markers & all_words_lower)

        if avg_words < 5 and avoidance_count > emotional_count:
            pattern = f"When under stress, {agent_id} tends to withdraw and give terse responses"
        elif emotional_count > avoidance_count:
            if reached_homeostasis:
                pattern = f"Under pressure, {agent_id} engages emotionally and works toward resolution"
            else:
                pattern = f"Under pressure, {agent_id} becomes emotionally expressive but struggles to find resolution"
        elif avg_words > 30:
            pattern = f"When stressed, {agent_id} tends to over-explain and rationalize"
        else:
            pattern = f"Under stress, {agent_id} maintains a measured, guarded communication style"

        return pattern

    @staticmethod
    def _extract_procedural_knowledge(
        post_crisis_transcript: List[Dict],
        reached_homeostasis: bool,
        elasticity_score: float,
    ) -> str:
        """Extract interaction pattern knowledge from a crisis outcome.

        Identifies which approaches appeared to help or hinder resolution.
        """
        if not post_crisis_transcript:
            return "Insufficient data to determine effective communication patterns."

        # Check for collaborative language
        all_text = " ".join(
            t.get("content", t.get("text", "")).lower() for t in post_crisis_transcript
        )
        has_collaborative = any(w in all_text for w in ["we", "us", "together", "let's", "both"])
        has_validation = any(w in all_text for w in ["understand", "hear you", "makes sense", "valid"])
        has_future = any(w in all_text for w in ["next time", "going forward", "from now", "we can"])

        if reached_homeostasis and elasticity_score > 0.6:
            strategies = []
            if has_collaborative:
                strategies.append("using collaborative 'we' language")
            if has_validation:
                strategies.append("validating the other person's experience")
            if has_future:
                strategies.append("reframing toward future-oriented solutions")
            if strategies:
                return f"Effective strategies during crisis: {', '.join(strategies)}"
            return "Resolution was reached through sustained engagement"

        if not reached_homeostasis:
            if not has_collaborative:
                return "Avoiding 'we' language during crisis correlated with collapse -- try collaborative framing next time"
            if not has_validation:
                return "Lack of explicit validation during crisis contributed to escalation"
            return "Despite effort, the approach used did not prevent collapse -- consider changing strategy"

        return "Crisis response was adequate but not strongly resilient"

    @staticmethod
    def _humanize_timestamp(timestamp: str) -> str:
        """Convert an ISO timestamp to a relative human-readable label.

        Since simulations don't map to real calendar time, this produces
        generic relative labels based on memory index position.
        """
        if not timestamp:
            return "some time ago"
        try:
            dt = datetime.fromisoformat(timestamp)
            now = datetime.now(timezone.utc)
            delta = now - dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else now - dt
            hours = delta.total_seconds() / 3600
            if hours < 1:
                return "just now"
            if hours < 24:
                return "earlier today"
            days = int(hours / 24)
            if days < 7:
                return f"{days} days ago"
            if days < 30:
                return f"{days // 7} weeks ago"
            return f"{days // 30} months ago"
        except (ValueError, TypeError):
            return "some time ago"

    def __repr__(self) -> str:
        return (
            f"RelationshipMemoryManager("
            f"pair_id={self._pair_id!r}, "
            f"memories={len(self._memory_index)})"
        )
