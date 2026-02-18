"""APRIORI CLI — Rich-powered interactive demo runner.

Commands:
    simulate   Run a full Monte Carlo relational simulation between two profiles.
    demo       Run a pre-loaded demo with Arjun (anxious) + Priya (avoidant).
    watch      Connect to a running API simulation and stream live progress.
    profile    Interactive shadow vector builder.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from apriori.models.shadow_vector import (
    SHADOW_VALUE_KEYS,
    AttachmentStyle,
    ShadowVector,
)

app = typer.Typer(name="apriori", help="APRIORI — Relational Foundation Model CLI")
console = Console()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "demo_profiles"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_shadow(path: str) -> ShadowVector:
    """Load a ShadowVector from a JSON file."""
    p = Path(path)
    if not p.exists():
        console.print(f"[red]File not found:[/red] {path}")
        raise typer.Exit(1)
    data = json.loads(p.read_text())
    return ShadowVector(**data)


def _profile_panel(shadow: ShadowVector) -> Panel:
    """Build a Rich Panel summarising a ShadowVector."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Key", style="dim")
    table.add_column("Value", style="bold")

    table.add_row("Agent ID", shadow.agent_id)
    table.add_row("Attachment", shadow.attachment_style.value.upper())
    table.add_row("Communication", shadow.communication_style)
    table.add_row("Entropy Tolerance", f"{shadow.entropy_tolerance:.2f}")
    table.add_row("Fears", ", ".join(shadow.fear_architecture))
    table.add_row("Takiya-kalaam", ", ".join(shadow.linguistic_signature))

    # Value dimensions as horizontal bar
    table.add_row("", "")
    for k in sorted(SHADOW_VALUE_KEYS):
        v = shadow.values[k]
        bar_len = int(v * 20)
        bar = "[green]" + "█" * bar_len + "[/green]" + "░" * (20 - bar_len)
        table.add_row(k.capitalize(), f"{bar} {v:.2f}")

    colour = {
        "anxious": "yellow",
        "avoidant": "blue",
        "secure": "green",
        "fearful": "red",
    }.get(shadow.attachment_style.value, "white")

    return Panel(
        table,
        title=f"[bold {colour}]{shadow.agent_id}[/bold {colour}]",
        border_style=colour,
        expand=False,
    )


def _vulnerability_table(
    axis: str, score: float, explanation: str
) -> Table:
    """Build a Rich Table showing shared vulnerability analysis."""
    t = Table(title="Shared Vulnerability Analysis", expand=True)
    t.add_column("Property", style="cyan")
    t.add_column("Value", style="white")
    t.add_row("Target Axis", f"[bold red]{axis.upper()}[/bold red]")
    t.add_row("Joint Vulnerability Score", f"{score:.4f}")
    t.add_row("Explanation", explanation)
    return t


def _survival_chart(survival_curve: List) -> str:
    """Render an ASCII bar chart for the survival curve."""
    if not survival_curve:
        return "  (no data)"
    lines: List[str] = []
    for thresh, rate in survival_curve:
        bar_len = int(rate * 40)
        bar = "█" * bar_len + "░" * (40 - bar_len)
        lines.append(f"  sev={thresh:.2f} │{bar}│ {rate:.0%}")
    return "\n".join(lines)


def _make_mock_llm():
    """Create a lightweight mock LLM client for demo/offline mode.

    Returns an AsyncMock that mirrors the contract expected by the
    core engines (returns objects with ``.content`` holding JSON strings).
    """
    from unittest.mock import AsyncMock

    class _Resp:
        def __init__(self, content: str) -> None:
            self.content = content

    def _neutral_deltas() -> str:
        return json.dumps({k: 0.0 for k in SHADOW_VALUE_KEYS})

    def _neutral_l2() -> str:
        return json.dumps({k: 0.5 for k in SHADOW_VALUE_KEYS})

    responses: Dict[str, str] = {
        "value_deltas": json.dumps(
            {k: (0.05 if k in ("intimacy", "belonging") else -0.02) for k in SHADOW_VALUE_KEYS}
        ),
        "l2_projection": _neutral_l2(),
        "l3_projection": _neutral_l2(),
        "strategy": json.dumps({"strategy": "probe", "rationale": "Gather more data."}),
        "defensive": json.dumps({"score": 0.15, "evidence": "Mild blame signal."}),
        "narrative": json.dumps(
            {"score": 0.12, "has_future_statements": True, "evidence": "Shared narrative mostly intact."}
        ),
        "verbalize": (
            "I feel the gap between who I am and who they think I am. "
            "It's small, but I notice it."
        ),
        "crisis_narrative": json.dumps({
            "narrative": (
                "Their startup's lead investor pulled out overnight. "
                "Three months of runway evaporated. "
                "The co-founder blamed the pitch — which Arjun led."
            ),
            "decision_point": "Face the fallout as a team, or retreat into individual coping.",
            "likely_a_reaction": "Arjun spirals into self-blame and seeks reassurance.",
            "likely_b_reaction": "Priya withdraws to process alone, needing space.",
        }),
    }

    def _decide(prompt: Any, **kwargs: Any) -> _Resp:
        text = str(prompt).lower()
        if "defensive attribution" in text or "blame" in text:
            return _Resp(responses["defensive"])
        if "narrative coherence" in text or "narrative incoherence" in text:
            return _Resp(responses["narrative"])
        if "crisis scenario" in text or "realistic crisis" in text:
            return _Resp(responses["crisis_narrative"])
        if "strategy" in text and "rationale" in text:
            return _Resp(responses["strategy"])
        if "fourth-order" in text or "l3" in text:
            return _Resp(responses["l3_projection"])
        if "projected persona" in text or "likely believes" in text:
            return _Resp(responses["l2_projection"])
        if "inner voice" in text or "inner monologue" in text:
            return _Resp(responses["verbalize"])
        if "implied importance shift" in text or "value dimension" in text:
            return _Resp(responses["value_deltas"])
        return _Resp(responses["value_deltas"])

    mock = AsyncMock()
    mock.ainvoke = AsyncMock(side_effect=_decide)
    return mock


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def simulate(
    profile_a: str = typer.Option(
        ..., "--profile-a", help="Path to JSON shadow vector for agent A"
    ),
    profile_b: str = typer.Option(
        ..., "--profile-b", help="Path to JSON shadow vector for agent B"
    ),
    n_timelines: int = typer.Option(
        10, "--timelines", "-n", help="Number of parallel simulations"
    ),
    max_turns: int = typer.Option(
        30, "--turns", help="Max turns per simulation"
    ),
    show_thoughts: bool = typer.Option(
        False, "--show-thoughts", help="Stream hidden thoughts from first timeline"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Save report to file"
    ),
) -> None:
    """Run a full Monte Carlo relational simulation between two profiles."""
    asyncio.run(
        _run_simulate(profile_a, profile_b, n_timelines, max_turns, show_thoughts, output)
    )


async def _run_simulate(
    profile_a_path: str,
    profile_b_path: str,
    n_timelines: int,
    max_turns: int,
    show_thoughts: bool,
    output: Optional[str],
) -> None:
    """Async implementation of the simulate command."""
    from apriori.core.event_generator import StochasticEventGenerator
    from apriori.core.monte_carlo import RelationalMonteCarlo

    # 1. Load profiles
    console.print()
    console.rule("[bold magenta]APRIORI — Relational Monte Carlo Simulation[/bold magenta]")
    console.print()

    shadow_a = _load_shadow(profile_a_path)
    shadow_b = _load_shadow(profile_b_path)

    console.print(_profile_panel(shadow_a))
    console.print()
    console.print(_profile_panel(shadow_b))
    console.print()

    # 2. Shared vulnerability analysis
    llm = _make_mock_llm()
    event_gen = StochasticEventGenerator(llm)
    axis, score, explanation = event_gen.identify_shared_vulnerability(shadow_a, shadow_b)

    console.print(_vulnerability_table(axis, score, explanation))
    console.print()

    # 3. Run Monte Carlo with progress bar
    pair_id = f"{shadow_a.agent_id}_x_{shadow_b.agent_id}"
    mc = RelationalMonteCarlo(
        llm_client=llm,
        n_timelines=n_timelines,
        max_turns_per_timeline=max_turns,
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Simulating {n_timelines} timelines...", total=n_timelines
        )

        def _on_progress(completed: int, total: int) -> None:
            progress.update(task, completed=completed)

        dist = await mc.run_ensemble(
            shadow_a, shadow_b, pair_id, progress_callback=_on_progress
        )

    console.print()

    # 4. If --show-thoughts: display first timeline's belief snapshots
    if show_thoughts and dist.timelines:
        first = dist.timelines[0]
        if first.belief_state_snapshots:
            console.rule("[bold cyan]Hidden Thoughts — Timeline 1[/bold cyan]")
            for snap in first.belief_state_snapshots[:5]:
                console.print(Panel(
                    json.dumps(snap, indent=2, default=str),
                    title=f"Turn {snap.get('turn', '?')}",
                    border_style="cyan",
                ))
            console.print()

    # 5. Executive report
    analysis = mc.analyze_distribution(dist)
    report = mc.generate_executive_report(dist, analysis)
    console.print(report)

    # 6. Survival curve
    survival = analysis.get("survival_curve", [])
    if survival:
        console.rule("[bold cyan]Survival Curve[/bold cyan]")
        console.print(_survival_chart(survival))
        console.print()

    # 7. Save output
    if output:
        out_path = Path(output)
        out_data = {
            "pair_id": pair_id,
            "n_simulations": dist.n_simulations,
            "homeostasis_rate": dist.homeostasis_rate,
            "antifragility_rate": dist.antifragility_rate,
            "median_elasticity": dist.median_elasticity,
            "p20_homeostasis": dist.p20_homeostasis,
            "p80_homeostasis": dist.p80_homeostasis,
            "primary_collapse_vector": dist.primary_collapse_vector,
            "collapse_attribution": dist.collapse_attribution,
            "analysis": {
                "homeostasis_by_severity_quartile": analysis.get("homeostasis_by_severity_quartile"),
                "survival_curve": analysis.get("survival_curve"),
                "confidence_intervals": {
                    k: list(v) for k, v in analysis.get("confidence_intervals", {}).items()
                },
                "risk_scenarios": analysis.get("risk_scenarios"),
                "recommendation": analysis.get("recommendation"),
            },
            "report": report,
        }
        out_path.write_text(json.dumps(out_data, indent=2, default=str))
        console.print(f"[green]Report saved to {out_path}[/green]")

    console.print("[bold green]Simulation complete.[/bold green]")


@app.command()
def demo() -> None:
    """Run a pre-loaded demo with Arjun (anxious, entrepreneur) + Priya (avoidant, artist).

    Uses hardcoded shadow vectors, injects startup failure crisis at turn 15.
    Shows full simulation in real-time.
    """
    arjun_path = _DATA_DIR / "arjun.json"
    priya_path = _DATA_DIR / "priya.json"

    if not arjun_path.exists() or not priya_path.exists():
        console.print("[red]Demo profiles not found.[/red]")
        console.print(f"Expected at: {_DATA_DIR}")
        raise typer.Exit(1)

    asyncio.run(_run_demo(str(arjun_path), str(priya_path)))


async def _run_demo(arjun_path: str, priya_path: str) -> None:
    """Async implementation of the demo command."""
    from apriori.core.event_generator import StochasticEventGenerator
    from apriori.core.monte_carlo import RelationalMonteCarlo

    console.print()
    console.rule("[bold magenta]APRIORI Demo — Arjun x Priya[/bold magenta]")
    console.print()
    console.print(
        "[dim]Anxious entrepreneur + Avoidant artist. "
        "Startup failure crisis injected at turn 15.[/dim]"
    )
    console.print()

    shadow_a = _load_shadow(arjun_path)
    shadow_b = _load_shadow(priya_path)

    # Display profiles
    console.print(_profile_panel(shadow_a))
    console.print()
    console.print(_profile_panel(shadow_b))
    console.print()

    # Shared vulnerability
    llm = _make_mock_llm()
    event_gen = StochasticEventGenerator(llm)
    axis, score, explanation = event_gen.identify_shared_vulnerability(shadow_a, shadow_b)

    console.print(_vulnerability_table(axis, score, explanation))
    console.print()

    # Generate a crisis event for display
    console.rule("[bold red]Crisis Injection Preview[/bold red]")
    crisis = await event_gen.generate_black_swan(
        shadow_a, shadow_b, severity_override=0.7, seed=42
    )
    crisis_table = Table(title="Black Swan Event", expand=True)
    crisis_table.add_column("Property", style="red")
    crisis_table.add_column("Value", style="white")
    crisis_table.add_row("Type", crisis.event_type.value)
    crisis_table.add_row("Target Axis", crisis.target_vulnerability_axis)
    crisis_table.add_row("Severity", f"{crisis.severity:.2f}")
    crisis_table.add_row("Elasticity Threshold", f"{crisis.elasticity_threshold:.2f}")
    crisis_table.add_row("Narrative", crisis.narrative_description)
    crisis_table.add_row("Decision Point", crisis.decision_point)
    console.print(crisis_table)
    console.print()

    # Run Monte Carlo (10 timelines for demo)
    n = 10
    pair_id = f"{shadow_a.agent_id}_x_{shadow_b.agent_id}"
    mc = RelationalMonteCarlo(
        llm_client=llm,
        n_timelines=n,
        max_turns_per_timeline=30,
        crisis_turn_range=(14, 16),  # force crisis near turn 15
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"Running {n} timelines...", total=n)

        def _on_progress(completed: int, total: int) -> None:
            progress.update(task, completed=completed)

        dist = await mc.run_ensemble(
            shadow_a, shadow_b, pair_id, progress_callback=_on_progress
        )

    console.print()

    # Report
    analysis = mc.analyze_distribution(dist)
    report = mc.generate_executive_report(dist, analysis)
    console.print(report)

    # Survival curve
    survival = analysis.get("survival_curve", [])
    if survival:
        console.rule("[bold cyan]Survival Curve[/bold cyan]")
        console.print(_survival_chart(survival))
        console.print()

    # Collapse attribution
    attr = dist.collapse_attribution
    if attr:
        console.rule("[bold yellow]Collapse Attribution[/bold yellow]")
        attr_table = Table(expand=True)
        attr_table.add_column("Crisis Axis", style="red")
        attr_table.add_column("Collapse Share", style="white", justify="right")
        for a, pct in attr.items():
            attr_table.add_row(a, f"{pct:.1%}")
        console.print(attr_table)
        console.print()

    console.print("[bold green]Demo complete.[/bold green]")


@app.command()
def watch(
    simulation_id: str = typer.Argument(..., help="Simulation ID from API"),
    api_url: str = typer.Option(
        "ws://localhost:8000", "--api-url", help="Base WebSocket URL"
    ),
) -> None:
    """Connect to a running API simulation and stream live progress."""
    asyncio.run(_run_watch(simulation_id, api_url))


async def _run_watch(simulation_id: str, api_url: str) -> None:
    """Async implementation of the watch command."""
    try:
        import websockets
    except ImportError:
        console.print("[red]Install websockets: pip install websockets[/red]")
        raise typer.Exit(1)

    ws_url = f"{api_url}/simulate/{simulation_id}/progress"
    console.print(f"[dim]Connecting to {ws_url}...[/dim]")

    try:
        async with websockets.connect(ws_url) as ws:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Watching simulation...", total=100)

                async for message in ws:
                    data = json.loads(message)
                    completed = data.get("completed", 0)
                    total = data.get("total", 100)
                    status = data.get("status", "running")
                    pct = data.get("percent", 0)

                    progress.update(
                        task,
                        completed=pct,
                        description=f"[{status}] {completed}/{total} timelines",
                    )

                    if status in ("completed", "cancelled", "failed"):
                        break

            console.print()
            if status == "completed":
                console.print("[bold green]Simulation completed![/bold green]")
                console.print(
                    f"[dim]Fetch report: curl localhost:8000/simulate/{simulation_id}/report[/dim]"
                )
            elif status == "cancelled":
                console.print("[bold yellow]Simulation was cancelled.[/bold yellow]")
            else:
                console.print(f"[bold red]Simulation ended with status: {status}[/bold red]")

    except Exception as exc:
        console.print(f"[red]Connection error: {exc}[/red]")
        console.print("[dim]Is the API server running?[/dim]")
        raise typer.Exit(1)


@app.command()
def profile(
    interactive: bool = typer.Option(
        True, "--interactive/--from-file", help="Build interactively or from file"
    ),
    output: str = typer.Option(
        "profile.json", "--output", "-o", help="Output file path"
    ),
) -> None:
    """Interactive shadow vector builder.

    Asks 8 questions (one per value dimension) + attachment style + fears.
    Outputs a JSON file ready for --profile-a / --profile-b.
    """
    if not interactive:
        console.print("[dim]Use --profile-a/--profile-b directly with existing JSON files.[/dim]")
        raise typer.Exit(0)

    console.print()
    console.rule("[bold magenta]APRIORI — Shadow Vector Builder[/bold magenta]")
    console.print()
    console.print(
        "[dim]Answer each question on a scale of 0.0 (not at all) to 1.0 (extremely). "
        "This builds a latent psychological profile.[/dim]"
    )
    console.print()

    # Agent ID
    agent_id = typer.prompt("Agent ID (e.g., your name)")

    # Value dimensions
    _questions = {
        "autonomy": "How important is personal independence and freedom to you?",
        "security": "How much do you value financial and emotional safety?",
        "achievement": "How driven are you by accomplishment and recognition?",
        "intimacy": "How important is deep emotional connection to you?",
        "novelty": "How much do you crave new experiences and change?",
        "stability": "How important is routine and predictability?",
        "power": "How much do you value influence and control over outcomes?",
        "belonging": "How important is feeling part of a group or community?",
    }

    values: Dict[str, float] = {}
    for key, question in _questions.items():
        while True:
            raw = typer.prompt(f"  [{key.upper()}] {question} (0.0-1.0)")
            try:
                val = float(raw)
                if 0.0 <= val <= 1.0:
                    values[key] = round(val, 2)
                    break
                console.print("[red]  Value must be between 0.0 and 1.0[/red]")
            except ValueError:
                console.print("[red]  Enter a decimal number[/red]")

    # Attachment style
    console.print()
    console.print("[bold]Attachment Style:[/bold]")
    console.print("  1. Secure — comfortable with closeness and independence")
    console.print("  2. Anxious — craves closeness, fears abandonment")
    console.print("  3. Avoidant — values independence, uncomfortable with dependency")
    console.print("  4. Fearful — desires closeness but fears rejection")

    style_map = {"1": "secure", "2": "anxious", "3": "avoidant", "4": "fearful"}
    while True:
        choice = typer.prompt("  Select (1-4)")
        if choice in style_map:
            attachment = style_map[choice]
            break
        console.print("[red]  Enter 1, 2, 3, or 4[/red]")

    # Fears
    console.print()
    fears_raw = typer.prompt(
        "Deepest fears (comma-separated, e.g. 'abandonment, failure, inadequacy')"
    )
    fears = [f.strip() for f in fears_raw.split(",") if f.strip()]

    # Linguistic signature
    console.print()
    phrases_raw = typer.prompt(
        "Signature phrases / takiya-kalaam (comma-separated, e.g. 'it's a vibe, sorted scene')"
    )
    phrases = [p.strip() for p in phrases_raw.split(",") if p.strip()]

    # Entropy tolerance
    while True:
        raw = typer.prompt("Entropy tolerance — how well do you handle chaos? (0.0=rigid, 1.0=fluid)")
        try:
            entropy = float(raw)
            if 0.0 <= entropy <= 1.0:
                break
            console.print("[red]  Value must be between 0.0 and 1.0[/red]")
        except ValueError:
            console.print("[red]  Enter a decimal number[/red]")

    # Communication style
    console.print()
    console.print("[bold]Communication Style:[/bold]")
    console.print("  1. Direct    — says what they mean")
    console.print("  2. Indirect  — hints, implies, reads between lines")
    console.print("  3. Aggressive — confrontational, forceful")
    console.print("  4. Passive   — avoids conflict, goes along")

    comm_map = {"1": "direct", "2": "indirect", "3": "aggressive", "4": "passive"}
    while True:
        choice = typer.prompt("  Select (1-4)")
        if choice in comm_map:
            comm_style = comm_map[choice]
            break
        console.print("[red]  Enter 1, 2, 3, or 4[/red]")

    # Build and validate
    shadow_data = {
        "agent_id": agent_id,
        "values": values,
        "attachment_style": attachment,
        "fear_architecture": fears,
        "linguistic_signature": phrases,
        "entropy_tolerance": round(entropy, 2),
        "communication_style": comm_style,
    }

    # Validate via Pydantic
    try:
        shadow = ShadowVector(**shadow_data)
    except Exception as exc:
        console.print(f"[red]Validation error: {exc}[/red]")
        raise typer.Exit(1)

    # Save
    out_path = Path(output)
    out_path.write_text(json.dumps(shadow_data, indent=4))

    console.print()
    console.print(_profile_panel(shadow))
    console.print()
    console.print(f"[bold green]Profile saved to {out_path}[/bold green]")
    console.print(
        f"[dim]Use with: apriori simulate --profile-a {out_path} --profile-b other.json[/dim]"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    app()
