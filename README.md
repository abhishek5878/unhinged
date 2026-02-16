# APRIORI — Relational Foundation Model

Predicts long-term relational homeostasis via Recursive Theory of Mind (R-ToM),
stochastic stress simulation, and multi-agent Monte Carlo trajectory analysis.

## Architecture

| Layer | Module | Purpose |
|-------|--------|---------|
| ToMTracker | `core/tom_tracker.py` | Recursive belief engine (L0→L3 epistemic loop) |
| StochasticEventGenerator | `core/event_generator.py` | Precision Black Swan injection on shared vulnerability axes |
| LinguisticAlignmentScorer | `core/alignment_scorer.py` | Cross-attention Hinglish convergence tracking |
| RelationalMonteCarlo | `core/monte_carlo.py` | 100-timeline parallel simulation runner |
| BeliefCollapseDetector | `core/collapse_detector.py` | KL-divergence early warning system |

### State Layers

Every agent maintains 4 simultaneous layers:

- **L0 — ShadowVector**: Ground truth latent state, never exposed in dialogue
- **L1 — Projected epistemic model**: What I believe about the other agent
- **L2 — Meta-epistemic projection**: What I think they think of me
- **L3 — Fourth-order recursive loop**: Optional, depth-gated

### Belief Collapse

Defined as `CoC(A,B,t) > VOC(A,B,t)` where CoC = coordination cost and
VOC = value of connection integral.

## Stack

Python 3.11, LangGraph, Temporal.io, Mem0, vLLM (Llama 3.1 70B),
indic-bert, Ray, FastAPI, PostgreSQL + pgvector, Redis, LangSmith

## Quick Start

```bash
cp .env.example .env
docker compose up -d
pip install -e ".[dev]"
pytest
```
