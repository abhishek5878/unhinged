"""Dialogue Graph -- Full LangGraph state machine for relational simulation.

Orchestrates the cyclic flow::

    hidden_thought_a -> generate_a -> hidden_thought_b -> generate_b ->
    linguistic_update -> homeostasis_check -> should_continue ->
        "continue"       -> hidden_thought_a   (loop)
        "check_collapse" -> collapse_check -> hidden_thought_a
        "inject_crisis"  -> crisis_injection -> hidden_thought_a
        "end"            -> END

Each turn pair (A speaks, B speaks) constitutes one full exchange. The graph
runs for up to ``max_turns`` exchanges, with optional crisis injection at a
configurable turn.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from apriori.core.alignment_scorer import LinguisticAlignmentScorer
from apriori.core.collapse_detector import BeliefCollapseDetector
from apriori.core.event_generator import StochasticEventGenerator
from apriori.core.tom_tracker import ToMTracker
from apriori.models.events import BlackSwanEvent
from apriori.models.shadow_vector import ShadowVector
from apriori.models.simulation import TimelineResult

# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------


class DialogueState(TypedDict):
    """Full mutable state flowing through the LangGraph.

    All Pydantic models are stored as dicts (via ``.model_dump()``) because
    LangGraph state must be JSON-serializable.
    """

    pair_id: str
    turn_number: int
    conversation_history: List[Dict]
    belief_state_a: Dict
    belief_state_b: Dict
    active_crisis: Optional[Dict]
    crisis_injected_at_turn: Optional[int]
    collapse_assessments: List[Dict]
    linguistic_convergence_log: List[Dict]
    simulation_complete: bool
    homeostasis_reached: bool
    final_resilience_score: float
    metadata: Dict


# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------

_AGENT_SYSTEM_PROMPT = """\
You are {agent_id} in a real relationship conversation. Embody the following \
identity naturally -- NEVER state your values directly. Show them through how you speak.

Attachment style: {attachment_style}
Communication style: {communication_style}
What matters most to you (DO NOT SAY THESE OUT LOUD): {top_values}
Your deepest fears (DO NOT REVEAL): {fears}

{crisis_context}\
{hidden_thought_context}

Linguistic signature -- weave these phrases in naturally when they fit:
{takiya_kalaam}
{memory_context}

Rules:
- Respond in 1-4 sentences. Natural dialogue, not monologues.
- React to what was ACTUALLY said, not what you know internally.
- If there's an active crisis, your response should reflect genuine emotional impact.
- You can use Hinglish if it feels natural to your character.
- DO NOT break character. DO NOT reference internal states or scores.\
"""


def _build_system_prompt(
    shadow: ShadowVector,
    hidden_thought: Optional[Dict],
    active_crisis: Optional[BlackSwanEvent],
    memory_context: str = "",
) -> str:
    """Construct the full system prompt for an agent's response generation.

    Weaves together persona, epistemic context, crisis narrative, and
    linguistic instructions into a single prompt that guides the LLM to
    produce in-character dialogue.
    """
    top_values = sorted(shadow.values.items(), key=lambda x: x[1], reverse=True)[:3]
    top_values_str = ", ".join(f"{k} ({v:.2f})" for k, v in top_values)
    fears_str = (
        ", ".join(shadow.fear_architecture) if shadow.fear_architecture else "none identified"
    )
    takiya_str = (
        ", ".join(f'"{p}"' for p in shadow.linguistic_signature)
        if shadow.linguistic_signature
        else "none"
    )

    # Crisis context block
    if active_crisis:
        crisis_context = (
            f"\nIMPORTANT -- A crisis has just occurred:\n"
            f"{active_crisis.narrative_description}\n"
            f"Decision point: {active_crisis.decision_point}\n"
            f"You must address this in your response.\n"
        )
    else:
        crisis_context = ""

    # Hidden thought context block
    if hidden_thought:
        l2 = hidden_thought.get("l2_projection", {})
        l2_top = sorted(l2.items(), key=lambda x: x[1], reverse=True)[:3] if l2 else []
        l2_str = ", ".join(f"{k}={v:.2f}" for k, v in l2_top) if l2_top else "unknown"
        ht_block = (
            f"\nYour inner state right now (use to guide tone, NOT content):\n"
            f"- You sense they value: {l2_str}\n"
            f"- Collapse risk: {hidden_thought.get('collapse_risk', 'LOW')}\n"
            f"- Strategy: {hidden_thought.get('recommended_strategy', 'be natural')}\n"
        )
    else:
        ht_block = "\nYour inner state: No prior read on this person yet. Be open.\n"

    mem_block = (
        f"\nMemories from your shared history:\n{memory_context}\n"
        if memory_context
        else ""
    )

    return _AGENT_SYSTEM_PROMPT.format(
        agent_id=shadow.agent_id,
        attachment_style=shadow.attachment_style.value,
        communication_style=shadow.communication_style,
        top_values=top_values_str,
        fears=fears_str,
        crisis_context=crisis_context,
        hidden_thought_context=ht_block,
        takiya_kalaam=takiya_str,
        memory_context=mem_block,
    )


def _format_history_for_prompt(history: List[Dict], last_n: int = 10) -> str:
    """Format recent conversation history into a string for the LLM prompt."""
    recent = history[-last_n:]
    lines = []
    for turn in recent:
        role = turn.get("role", "unknown")
        content = turn.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines) if lines else "(conversation just started)"


# ---------------------------------------------------------------------------
# Node factory
# ---------------------------------------------------------------------------


def _make_nodes(
    tom_a: ToMTracker,
    tom_b: ToMTracker,
    ling: LinguisticAlignmentScorer,
    collapse: BeliefCollapseDetector,
    shadow_a: ShadowVector,
    shadow_b: ShadowVector,
    llm: Any,
    max_turns: int,
    crisis_turn: int,
    evt_gen: Optional[StochasticEventGenerator],
    crisis_event: Optional[BlackSwanEvent],
) -> Dict[str, Any]:
    """Create all graph node functions as closures over shared simulation components.

    Each node is an ``async def`` accepting a :class:`DialogueState` and returning
    a partial state update dict. LangGraph merges the returned dict into the
    running state automatically.
    """

    _crisis: Dict[str, Optional[BlackSwanEvent]] = {"event": crisis_event}

    # ------------------------------------------------------------------
    # hidden_thought_a
    # ------------------------------------------------------------------
    async def node_hidden_thought_a(state: DialogueState) -> Dict[str, Any]:
        """Agent A's internal epistemic update BEFORE generating a response.

        Calls ``tom_tracker_a.hidden_thought()`` with the last B utterance.
        Updates ``belief_state_a`` but does NOT touch ``conversation_history``.
        """
        history = state["conversation_history"]
        last_b = ""
        for turn in reversed(history):
            if turn.get("role") == shadow_b.agent_id:
                last_b = turn.get("content", "")
                break

        await tom_a.hidden_thought(
            shadow_b.agent_id,
            last_b or "(conversation starting)",
            history,
        )
        return {"belief_state_a": tom_a.get_belief_state().model_dump()}

    # ------------------------------------------------------------------
    # generate_response_a
    # ------------------------------------------------------------------
    async def node_generate_response_a(state: DialogueState) -> Dict[str, Any]:
        """Agent A generates a dialogue response.

        System prompt construction:
        - Base persona from ``shadow_a`` (attachment, values, communication style).
        - MUST NOT directly state values -- embody them naturally.
        - Current hidden-thought context (L2 projection, recommended strategy).
        - Active crisis context if injected.
        - Conversation history (last 10 turns).
        - Linguistic instructions: use ``shadow_a``'s takiya-kalaam naturally.

        Appends the new turn to ``conversation_history``.
        """
        history = state["conversation_history"]
        thought_log = tom_a.get_thought_log(last_n=1)
        latest_thought = thought_log[0] if thought_log else None

        active = (
            BlackSwanEvent(**state["active_crisis"])
            if state.get("active_crisis")
            else None
        )

        system_prompt = _build_system_prompt(shadow_a, latest_thought, active)
        history_str = _format_history_for_prompt(history)

        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if history:
            messages.append({
                "role": "user",
                "content": f"Conversation so far:\n{history_str}\n\nRespond as {shadow_a.agent_id}.",
            })
        else:
            messages.append({
                "role": "user",
                "content": f"Start the conversation as {shadow_a.agent_id}. Say something natural to open.",
            })

        response = await llm.ainvoke(messages)
        content = (response.content if hasattr(response, "content") else str(response)).strip()

        new_turn = {
            "role": shadow_a.agent_id,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        ling.ingest_turn(shadow_a.agent_id, content)

        return {"conversation_history": history + [new_turn]}

    # ------------------------------------------------------------------
    # hidden_thought_b
    # ------------------------------------------------------------------
    async def node_hidden_thought_b(state: DialogueState) -> Dict[str, Any]:
        """Agent B's internal epistemic update. Symmetric to ``node_hidden_thought_a``."""
        history = state["conversation_history"]
        last_a = ""
        for turn in reversed(history):
            if turn.get("role") == shadow_a.agent_id:
                last_a = turn.get("content", "")
                break

        if last_a:
            await tom_b.hidden_thought(shadow_a.agent_id, last_a, history)

        return {"belief_state_b": tom_b.get_belief_state().model_dump()}

    # ------------------------------------------------------------------
    # generate_response_b
    # ------------------------------------------------------------------
    async def node_generate_response_b(state: DialogueState) -> Dict[str, Any]:
        """Agent B generates a dialogue response. Symmetric to ``node_generate_response_a``."""
        history = state["conversation_history"]
        thought_log = tom_b.get_thought_log(last_n=1)
        latest_thought = thought_log[0] if thought_log else None

        active = (
            BlackSwanEvent(**state["active_crisis"])
            if state.get("active_crisis")
            else None
        )

        system_prompt = _build_system_prompt(shadow_b, latest_thought, active)
        history_str = _format_history_for_prompt(history)

        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        messages.append({
            "role": "user",
            "content": f"Conversation so far:\n{history_str}\n\nRespond as {shadow_b.agent_id}.",
        })

        response = await llm.ainvoke(messages)
        content = (response.content if hasattr(response, "content") else str(response)).strip()

        new_turn = {
            "role": shadow_b.agent_id,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        ling.ingest_turn(shadow_b.agent_id, content)

        return {
            "conversation_history": history + [new_turn],
            "turn_number": state["turn_number"] + 1,
        }

    # ------------------------------------------------------------------
    # linguistic_update
    # ------------------------------------------------------------------
    async def node_linguistic_update(state: DialogueState) -> Dict[str, Any]:
        """After each full A+B exchange, compute linguistic convergence.

        Ingestion already happens in the generate nodes. This node runs the
        full convergence analysis and checks for withdrawal signals.
        """
        convergence = ling.compute_convergence(shadow_a.agent_id, shadow_b.agent_id)
        record = {
            "turn": state["turn_number"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **convergence,
        }
        return {
            "linguistic_convergence_log": state["linguistic_convergence_log"] + [record],
        }

    # ------------------------------------------------------------------
    # collapse_check
    # ------------------------------------------------------------------
    async def node_collapse_check(state: DialogueState) -> Dict[str, Any]:
        """Run ``BeliefCollapseDetector.assess()`` every 3 turns.

        Appends the full assessment dict (with turn number) to
        ``collapse_assessments``.
        """
        assessment = await collapse.assess(state["conversation_history"])
        assessment["turn"] = state["turn_number"]
        return {
            "collapse_assessments": state["collapse_assessments"] + [assessment],
        }

    # ------------------------------------------------------------------
    # crisis_injection
    # ------------------------------------------------------------------
    async def node_crisis_injection(state: DialogueState) -> Dict[str, Any]:
        """Inject a crisis narrative into the conversation as a SYSTEM message.

        Format::

            [EXTERNAL EVENT]: {narrative_description}

            [DECISION POINT]: {decision_point}

        Sets ``active_crisis`` and ``crisis_injected_at_turn``. Agents must
        respond to this event in subsequent turns.
        """
        crisis = _crisis["event"]
        if crisis is None and evt_gen is not None:
            crisis = await evt_gen.generate_black_swan(shadow_a, shadow_b)
            _crisis["event"] = crisis

        if crisis is None:
            return {}

        crisis_message = {
            "role": "SYSTEM",
            "content": (
                f"[EXTERNAL EVENT]: {crisis.narrative_description}\n\n"
                f"[DECISION POINT]: {crisis.decision_point}"
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return {
            "conversation_history": state["conversation_history"] + [crisis_message],
            "active_crisis": crisis.model_dump(),
            "crisis_injected_at_turn": state["turn_number"],
        }

    # ------------------------------------------------------------------
    # homeostasis_check
    # ------------------------------------------------------------------
    async def node_homeostasis_check(state: DialogueState) -> Dict[str, Any]:
        """Check if the relationship has reached stable homeostasis.

        Criteria:
            1. No CRITICAL collapse events in the last 5 assessments.
            2. Linguistic convergence trend is ``"stable"`` or ``"accelerating"``.
            3. Both agents are making future-oriented statements (we/our/together
               in recent turns).
            4. If a crisis occurred, the latest resilience delta exceeds the
               crisis elasticity threshold.
            5. At least 8 turns have elapsed.

        Sets ``homeostasis_reached`` and computes ``final_resilience_score``.
        """
        assessments = state["collapse_assessments"]
        conv_log = state["linguistic_convergence_log"]
        history = state["conversation_history"]
        turn = state["turn_number"]

        # 1. No CRITICAL in last 5 assessments
        recent_a = assessments[-5:] if assessments else []
        no_critical = all(a.get("risk_level") != "CRITICAL" for a in recent_a)

        # 2. Convergence trend
        latest_conv = conv_log[-1] if conv_log else {}
        trend = latest_conv.get("convergence_trend", "stable")
        trend_ok = trend in ("stable", "accelerating")

        # 3. Future-oriented statements in last 5 agent turns
        future_markers = {"we", "us", "our", "together", "we'll", "we'd", "let's"}
        agent_turns = [t for t in history[-5:] if t.get("role") != "SYSTEM"]
        has_future = any(
            future_markers & set(t.get("content", "").lower().split())
            for t in agent_turns
        )

        # 4. Crisis elasticity check
        crisis_ok = True
        if state.get("active_crisis"):
            crisis = BlackSwanEvent(**state["active_crisis"])
            latest_resilience = latest_conv.get("resilience_delta", 0.5)
            crisis_ok = latest_resilience > crisis.elasticity_threshold

        homeostasis = no_critical and trend_ok and has_future and crisis_ok and turn >= 8

        # Final resilience score
        if recent_a:
            avg_risk = sum(a.get("overall_collapse_risk", 0.5) for a in recent_a) / len(recent_a)
            resilience = 1.0 - avg_risk
        else:
            resilience = 0.5

        if conv_log:
            resilience = min(1.0, resilience + latest_conv.get("resilience_delta", 0.0) * 0.3)

        return {
            "homeostasis_reached": homeostasis,
            "final_resilience_score": round(resilience, 4),
        }

    # ------------------------------------------------------------------
    # should_continue (conditional edge)
    # ------------------------------------------------------------------
    def should_continue(state: DialogueState) -> str:
        """Determine the next step in the graph.

        Returns
        -------
        str
            ``"end"`` -- simulation complete or max turns reached.
            ``"inject_crisis"`` -- crisis should be injected this turn.
            ``"check_collapse"`` -- ``turn_number % 3 == 0``.
            ``"continue"`` -- proceed to next exchange.
        """
        if state.get("simulation_complete"):
            return "end"
        turn = state["turn_number"]
        if turn >= max_turns:
            return "end"
        if turn == crisis_turn and state.get("crisis_injected_at_turn") is None:
            return "inject_crisis"
        if turn > 0 and turn % 3 == 0:
            return "check_collapse"
        return "continue"

    return {
        "node_hidden_thought_a": node_hidden_thought_a,
        "node_generate_response_a": node_generate_response_a,
        "node_hidden_thought_b": node_hidden_thought_b,
        "node_generate_response_b": node_generate_response_b,
        "node_linguistic_update": node_linguistic_update,
        "node_collapse_check": node_collapse_check,
        "node_crisis_injection": node_crisis_injection,
        "node_homeostasis_check": node_homeostasis_check,
        "should_continue": should_continue,
    }


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------


def build_dialogue_graph(
    shadow_a: ShadowVector,
    shadow_b: ShadowVector,
    llm_client: Any,
    max_turns: int = 40,
    crisis_at_turn: int = 15,
    recursion_depth: int = 2,
    event_generator: Optional[StochasticEventGenerator] = None,
    pre_generated_crisis: Optional[BlackSwanEvent] = None,
) -> CompiledStateGraph:
    """Assemble and compile the full LangGraph dialogue state machine.

    Initializes all core components (ToMTrackers, LinguisticAlignmentScorer,
    BeliefCollapseDetector), wires them into graph nodes, and compiles the
    graph with a memory-based checkpointer.

    Parameters
    ----------
    shadow_a, shadow_b:
        Ground-truth shadow vectors for both agents.
    llm_client:
        LangChain chat model (used for both ToM inference and response generation).
    max_turns:
        Maximum number of full exchanges before forced termination.
    crisis_at_turn:
        Turn number at which to inject a Black Swan event.
    recursion_depth:
        ToM recursion depth (2 = up to L2, 3 = includes L3 fourth-order loop).
    event_generator:
        Optional stochastic event generator. If ``None``, crisis injection is
        skipped unless ``pre_generated_crisis`` is provided.
    pre_generated_crisis:
        Optional pre-generated crisis event to inject instead of generating one.

    Returns
    -------
    CompiledStateGraph
        Compiled LangGraph with memory saver and ``interrupt_before`` on the
        crisis injection node (so the caller can preview the crisis before
        it enters the dialogue).
    """
    tom_a = ToMTracker(
        shadow_a.agent_id, shadow_a, llm_client, recursion_depth=recursion_depth
    )
    tom_b = ToMTracker(
        shadow_b.agent_id, shadow_b, llm_client, recursion_depth=recursion_depth
    )
    ling = LinguisticAlignmentScorer()
    detector = BeliefCollapseDetector(tom_a, tom_b, ling, llm_client)

    nodes = _make_nodes(
        tom_a=tom_a,
        tom_b=tom_b,
        ling=ling,
        collapse=detector,
        shadow_a=shadow_a,
        shadow_b=shadow_b,
        llm=llm_client,
        max_turns=max_turns,
        crisis_turn=crisis_at_turn,
        evt_gen=event_generator,
        crisis_event=pre_generated_crisis,
    )

    graph = StateGraph(DialogueState)

    # Register nodes
    graph.add_node("hidden_thought_a", nodes["node_hidden_thought_a"])
    graph.add_node("generate_response_a", nodes["node_generate_response_a"])
    graph.add_node("hidden_thought_b", nodes["node_hidden_thought_b"])
    graph.add_node("generate_response_b", nodes["node_generate_response_b"])
    graph.add_node("linguistic_update", nodes["node_linguistic_update"])
    graph.add_node("collapse_check", nodes["node_collapse_check"])
    graph.add_node("crisis_injection", nodes["node_crisis_injection"])
    graph.add_node("homeostasis_check", nodes["node_homeostasis_check"])

    # Entry point
    graph.set_entry_point("hidden_thought_a")

    # Linear chain per exchange
    graph.add_edge("hidden_thought_a", "generate_response_a")
    graph.add_edge("generate_response_a", "hidden_thought_b")
    graph.add_edge("hidden_thought_b", "generate_response_b")
    graph.add_edge("generate_response_b", "linguistic_update")
    graph.add_edge("linguistic_update", "homeostasis_check")

    # Conditional branching after homeostasis check
    graph.add_conditional_edges(
        "homeostasis_check",
        nodes["should_continue"],
        {
            "continue": "hidden_thought_a",
            "check_collapse": "collapse_check",
            "inject_crisis": "crisis_injection",
            "end": END,
        },
    )

    # Return edges from ancillary nodes
    graph.add_edge("collapse_check", "hidden_thought_a")
    graph.add_edge("crisis_injection", "hidden_thought_a")

    memory = MemorySaver()
    return graph.compile(
        checkpointer=memory,
        interrupt_before=["crisis_injection"],
    )


# ---------------------------------------------------------------------------
# High-level simulation runner
# ---------------------------------------------------------------------------


async def run_simulation(
    shadow_a: ShadowVector,
    shadow_b: ShadowVector,
    llm_client: Any,
    event_generator: StochasticEventGenerator,
    max_turns: int = 40,
    crisis_at_turn: int = 15,
    seed: Optional[int] = None,
) -> TimelineResult:
    """High-level runner: builds graph, generates crisis, runs to completion.

    This is the main entry point for running a single simulated timeline.
    Pre-generates the crisis event, builds the dialogue graph, and streams
    it to completion (automatically resuming past the crisis-injection
    interrupt).

    Parameters
    ----------
    shadow_a, shadow_b:
        Agent shadow vectors.
    llm_client:
        LangChain chat model.
    event_generator:
        Stochastic event generator for crisis creation.
    max_turns:
        Maximum number of full exchanges.
    crisis_at_turn:
        Turn at which to inject the crisis.
    seed:
        Random seed for reproducible crisis generation.

    Returns
    -------
    TimelineResult
        Fully populated result with transcript, belief snapshots, and metrics.
    """
    from uuid import uuid4

    crisis = await event_generator.generate_black_swan(shadow_a, shadow_b, seed=seed)
    pair_id = f"{shadow_a.agent_id}_{shadow_b.agent_id}"

    graph = build_dialogue_graph(
        shadow_a=shadow_a,
        shadow_b=shadow_b,
        llm_client=llm_client,
        max_turns=max_turns,
        crisis_at_turn=crisis_at_turn,
        event_generator=event_generator,
        pre_generated_crisis=crisis,
    )

    initial_state: DialogueState = {
        "pair_id": pair_id,
        "turn_number": 0,
        "conversation_history": [],
        "belief_state_a": {},
        "belief_state_b": {},
        "active_crisis": None,
        "crisis_injected_at_turn": None,
        "collapse_assessments": [],
        "linguistic_convergence_log": [],
        "simulation_complete": False,
        "homeostasis_reached": False,
        "final_resilience_score": 0.0,
        "metadata": {
            "seed": seed,
            "max_turns": max_turns,
            "crisis_at_turn": crisis_at_turn,
        },
    }

    config = {"configurable": {"thread_id": str(uuid4())}}

    # Stream the graph, collecting the final state
    final_state: Dict[str, Any] = dict(initial_state)
    async for event in graph.astream(initial_state, config=config):
        for _node_name, node_output in event.items():
            if isinstance(node_output, dict):
                final_state.update(node_output)

    # Handle interrupt-resume cycle (crisis injection)
    snapshot = graph.get_state(config)
    while snapshot.next:
        async for event in graph.astream(None, config=config):
            for _node_name, node_output in event.items():
                if isinstance(node_output, dict):
                    final_state.update(node_output)
        snapshot = graph.get_state(config)

    # Extract metrics from final state
    collapse_assessments = final_state.get("collapse_assessments", [])
    convergence_log = final_state.get("linguistic_convergence_log", [])

    belief_snapshots = [
        {
            "turn": a.get("turn", 0),
            "risk": a.get("overall_collapse_risk", 0.0),
            "risk_level": a.get("risk_level", "STABLE"),
            "signal_breakdown": a.get("signal_breakdown", {}),
        }
        for a in collapse_assessments
    ]

    collapse_count = sum(
        1 for a in collapse_assessments if a.get("risk_level") in ("CRITICAL", "HIGH")
    )

    final_convergence = (
        convergence_log[-1].get("resilience_delta", 0.5) if convergence_log else 0.5
    )

    final_resilience = final_state.get("final_resilience_score", 0.5)
    antifragile = (
        final_resilience > 0.6
        and final_state.get("crisis_injected_at_turn") is not None
    )

    return TimelineResult(
        seed=seed or 0,
        pair_id=pair_id,
        crisis_severity=crisis.severity,
        crisis_axis=crisis.target_vulnerability_axis,
        reached_homeostasis=final_state.get("homeostasis_reached", False),
        narrative_elasticity=min(1.0, max(0.0, final_convergence)),
        final_resilience_score=final_resilience,
        antifragile=antifragile,
        turns_total=final_state.get("turn_number", 0),
        belief_collapse_events=collapse_count,
        linguistic_convergence_final=round(final_convergence, 4),
        full_transcript=final_state.get("conversation_history", []),
        belief_state_snapshots=belief_snapshots,
    )
