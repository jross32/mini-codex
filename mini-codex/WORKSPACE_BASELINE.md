# Workspace Baseline — March 25, 2026

## Current Accepted Baseline

**AISH v1 — trust-gated orchestrator + toolmaker active**

- Symbol_graph exists as isolated prototype (JSON artifacts in workspace root, not wired to planner)
- No `--use-symbol-graph` flag anywhere in AISH CLI (removed in March 24 cleanup)
- Core agent operates on import-frequency heuristics for file selection
- Orchestrator (`agent/orchestrator.py`) is active with trust-gated autonomous worker spawning
- Toolmaker (`ai_repo_tools/tools/toolmaker/`) is active and used during upgrade/orchestrate runs

## Accepted Working Paths

- **Single inspection:** `python -m aish inspect --goal "..." --repo <path> [--max-steps N]`
- **Self-upgrade loop:** `python -m aish upgrade --repo <path> [--iterations N]`
- **Trust-gated orchestrator:** `python -m aish orchestrate --repo <path> [--iterations N] [--trust-threshold F] [--max-workers N] [--unbounded]`
  - `--max-workers` is optional; AISH prompts interactively if omitted
  - Default trust threshold: 0.84
  - Default max workers: prompted (fallback: 16 in non-interactive mode)
- **Auto-routing:** `python -m aish auto --goal "..." --repo <path>`
- **Direct tool call:** `python -m aish tool <tool_name> --repo <path> [args...]`
- **Direct agent loop (escape hatch only):** `python -m agent.agent_loop --goal "..." --repo <path> --max-steps N`

## Current Repo Truth

- **AISH surface is clean:** no dead flags, no dead parameters
- **Orchestrator is live:** `agent/orchestrator.py` implements 4 worker phases + trust-gated autonomous spawn
  - `toolkit_upgrade_worker` → `repo_inspector_worker` → `quality_gate_worker` → `agent_core_upgrade_worker`
  - Trusted workers may spawn additional `autonomous_worker_N` instances up to `max_total_workers` cap
- **Toolmaker is active:** `ai_repo_tools/tools/toolmaker/` provides `agent_audit` and `agent_improver`
- **Quality gate is deterministic:** uses `repo_health_check`, `lint_check` tools (not heuristics)
- **Symbol_graph prototype artifacts exist but are not wired in:**
  - `symbol_graph_Trade.json`, `symbol_graph_apaR.json`, `symbol_graph_cog.json`, `symbol_graph_myLife.json`, `symbol_graph_LifeOS_2.json`
  - Preserved for future Phase 2 planner integration

## Trust Scoring (Orchestrator)

A worker earns trust based on:
- 45% — success rate across steps
- 20% — average usefulness score
- 20% — average next-step quality
- 10% — self-improvement readiness (has used `tool_audit`/`agent_audit` + `tool_improver`/`agent_improver` + `lint_check`)
- 5%  — collaboration readiness (successful peers exist + tooling signals)

Trusted workers (score ≥ threshold AND self-improve-ready AND collaboration-ready) may spawn additional workers.

## Known Deferred Work

- Symbol_graph planner integration: NOT active; Phase 2 candidate, value unproven
- Formal test suite for orchestrate CLI prompt path and spawn-gate benchmarks
- apaR initial file selection reads venv deps — known heuristic issue, not addressed

## What Must Not Change Accidentally

- ❌ No `--use-symbol-graph` or similar dead flags re-introduced
- ❌ No hidden experimental wiring in planner without explicit approval
- ❌ No unbounded worker growth without explicit `--unbounded` flag
- ❌ Trust threshold must not be lowered below 0.84 without validated benchmark evidence

## Baseline History

| Date | Action |
|------|--------|
| 2026-03-24 | Removed dead symbol_graph wiring; frozen AISH v0 baseline |
| 2026-03-25 | Added orchestrator, toolmaker, trust-gated worker spawning, interactive max-worker prompt; AISH v1 baseline |
