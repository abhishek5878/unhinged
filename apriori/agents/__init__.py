from apriori.agents.base_agent import BaseRelationalAgent

# Lazy imports for dialogue_graph (requires langgraph) and memory_manager (requires mem0)
# to avoid ImportError when dependencies aren't installed (e.g. in test environments).


def __getattr__(name: str):
    if name in ("DialogueState", "build_dialogue_graph", "run_simulation"):
        from apriori.agents.dialogue_graph import (
            DialogueState,
            build_dialogue_graph,
            run_simulation,
        )
        return {"DialogueState": DialogueState, "build_dialogue_graph": build_dialogue_graph, "run_simulation": run_simulation}[name]
    if name == "RelationshipMemoryManager":
        from apriori.agents.memory_manager import RelationshipMemoryManager
        return RelationshipMemoryManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BaseRelationalAgent",
    "DialogueState",
    "RelationshipMemoryManager",
    "build_dialogue_graph",
    "run_simulation",
]
