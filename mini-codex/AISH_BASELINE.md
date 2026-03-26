# AISH v1 Baseline

**Status:** Accepted as production baseline ✓

**Date:** 2026-03-25 (updated from v0 baseline of 2026-03-24)

---

## What AISH v1 Is

AISH v1 is the primary command layer for the mini-codex self-improving agent framework. It dispatches to the agent loop, orchestrator, and tool registry. New in v1: orchestrate with trust-gated worker spawning, self-upgrade loop, direct tool invocation, and auto-routing.

As of the latest update, AISH also supports:
- formal command contract metadata and safety tiers
- machine-readable JSON envelope output (`--json`)
- caller role routing (`--as-role worker|orchestrator|admin|user`)
- expanded command families (`list-tools`, `tool-info`, `run-tool`, `validate-tool`, `benchmark-tool`, `compare-tool`, `show-report`)
- automated tool validation command (`test-tools`)
- explicit mutation guardrail for `bulk_tool_generator` (`--user-approved-generator` required; blocked for worker/orchestrator roles)

---

## Supported Commands

### `aish map <repo>`
List all files in a repository. Calls `repo_map` tool.

### `aish read <path> [--repo <path>]`
Read and summarize a file. Calls `ai_read` tool. Displays file metadata, imports, functions, classes, and preview.

### `aish inspect --goal "..." --repo <path> [--max-steps N]`
Run full repository analysis with agent loop. Calls `agent_loop` which internally invokes repo_map, ai_read, and test_select. Records each tool invocation separately.

### `aish upgrade --repo <path> [--iterations N]`
Run friction-driven self-upgrade loop: audit → improve → lint → validate. Uses toolmaker tools (`agent_audit`, `agent_improver`) via the agent loop.

### `aish orchestrate --repo <path> [--iterations N] [--trust-threshold F] [--max-workers N] [--unbounded]`
Run trust-gated multi-worker orchestrator. Executes four sequential worker phases:
1. `toolkit_upgrade_worker` — improve toolkit with toolmaker
2. `repo_inspector_worker` — inspect architecture
3. `quality_gate_worker` — deterministic lint/health checks
4. `agent_core_upgrade_worker` — bounded agent-core policy tuning

Workers that pass the trust gate may autonomously spawn additional workers (up to `--max-workers` cap).
- `--trust-threshold` (default: 0.84): minimum composite trust score to allow spawning
- `--max-workers` (optional): cap on total workers; if omitted, AISH prompts interactively
- `--unbounded`: remove hard cap (not recommended for production)

### `aish tool <tool_name> --repo <path> [args...]`
Call any ai_repo_tools tool directly through AISH auto mode.

### `aish run-tool <tool_name> --repo <path> [args...]`
Alias for `aish tool`.

### `aish list-tools [--category <name>]`
List available toolkit tools from registry metadata.

### `aish tool-info <tool_name>`
Show metadata for a single tool: category, args, and returns.

### `aish validate-tool <tool_name> --repo <path>`
Validate a tool command module through `cmd_run`.

### `aish benchmark-tool <tool_name> --repo <path> [args...]`
Benchmark tool runs; delegates to `bench_compare` for `fast_process`.

### `aish test-tools [--tool <name>] [--case <name>] [--verbose]`
Run the `ai_repo_tools/validations/runner.py` suite for quick automated tool validation.

### `aish compare-tool <tool_name> --repo <path> --old <path> --new <path>`
Compare local files/artifacts via `diff_check`.

### `aish show-report <path> [--repo <path>]`
Summarize a local report/log artifact via `artifact_read`.

### `aish auto [--goal "..."] [--repo <path>] [--path <file>] [--max-steps N]`
Auto-route based on available inputs: map if only repo, read if only file, inspect if goal+repo.

### `aish usage`
Display aggregate command and tool usage statistics. Shows:
- Total invocations per command (map, read, inspect, upgrade, orchestrate, tool, auto, usage)
- Total calls per underlying tool
- Timestamp of last update

### `--json` global flag
Wraps command output in a consistent envelope:
- `success`
- `exit_code`
- `summary`
- `stdout` / `stderr`
- command contract metadata

### `--as-role` global flag
Applies safety policy for automation callers (`worker`, `orchestrator`, `admin`, `user`).

---

## Repository Placement

```
mini-codex/
├── aish/                    ← AISH v1 module
│   ├── __init__.py         (version metadata)
│   ├── __main__.py         (entry point for python -m aish)
│   ├── cli.py              (argument parsing, dispatch)
│   ├── commands.py         (command implementations including orchestrate_agents)
│   └── usage.py            (UsageTracker, statistics aggregation)
├── agent/
│   ├── agent_loop.py       (RepoAgent core)
│   ├── orchestrator.py     (trust-gated multi-worker orchestrator) ← NEW in v1
│   └── ...
├── ai_repo_tools/
│   └── tools/toolmaker/    (agent_audit, agent_improver tools) ← NEW in v1
├── agent_logs/
│   ├── aish_usage.json     (AISH command/tool tracking)
│   └── orchestrator_summary.json (written per orchestrate run) ← NEW in v1
└── ...
```

---

## Logs and Artifacts

### agent_logs/aish_usage.json
Append-only JSON log of all AISH command invocations. One record per line:

```json
{
  "timestamp": "2026-03-24T22:15:27.171626Z",
  "command": "inspect",
  "tool": "agent_loop",
  "success": true
}
```

Records track:
- When each command was invoked
- What underlying tool was used
- Success/failure status

This log is read by `aish usage` to generate aggregate statistics.

### agent_logs/agent_run.log
Existing agent execution log. AISH does not modify this. Used only to extract tool sequence from most recent run.

---

## What AISH Deliberately Does NOT Do

- **No interactive shell** — Commands are one-shot; no REPL or streaming responses
- **No state management** — Each command is independent; no session or context persistence
- **No planner symbol-graph wiring** — Symbol_graph prototype artifacts exist but are not consumed

---

## Acceptance Testing & Results

### Test: Single-Run Tool Tracking

**Setup:** Ran aish inspect once on test_repo with max-steps=5

**Before:**
```
inspect: 313
repo_map: 75
ai_read: 168
agent_loop: 6
test_select: 68
```

**After:**
```
inspect: 314
repo_map: 76
ai_read: 169
agent_loop: 7
test_select: 69
```

**Delta:** Each +1 ✓

**Conclusion:** AISH correctly records exactly one inspect invocation and one underlying tool usage per tool called during that run. No overcounting, no historical replay.

### Test: File Coverage

- ✓ cli.py — Argument parsing, dispatch routing
- ✓ commands.py — map_repo, read_file, inspect_repo, show_usage implementations
- ✓ usage.py — UsageTracker, log aggregation
- ✓ __init__.py — Version metadata
- ✓ __main__.py — Entry point for `python -m aish`

### Test: Command Coverage

- ✓ map — Lists repository files
- ✓ read — Reads file with metadata
- ✓ inspect — Runs agent loop, captures underlying tool usage
- ✓ upgrade — Runs self-upgrade loop via toolmaker
- ✓ orchestrate — Runs trust-gated multi-worker workflow; writes orchestrator_summary.json
- ✓ tool — Calls any ai_repo_tools tool directly
- ✓ auto — Auto-routes to map/read/inspect based on available inputs
- ✓ usage — Displays aggregate statistics

All commands tested and functional.

---

## Known Limitations

### 1. UTF-16 Preview Issue (Inherited from ai_read)

**Symptom:** File previews in `aish read` may show corrupted characters (`ÿþ` and escaped unicode).

**Root Cause:** 
- Some files in test repos are UTF-16 LE encoded (BOM: 0xFF 0xFE)
- `ai_read` tool does not decode encoding; returns raw bytes as JSON-escaped unicode
- AISH displays what it receives

**Status:** Known limitation, not a bug in AISH. Would require ai_read changes to fix.

**Workaround:** None in AISH v0. Acceptable for analysis workflows (metadata is readable, preview is supplementary).

### 2. Shallow Tool Tracking

**Scope:** AISH tracks tool usage at command level, not per-step or per-parameter.

**Example:** `inspect` records one repo_map call, not distinguishing between calls with different arguments or results.

**Status:** Acceptable for AISH v0. Full call-graph tracking would require changes to agent internals.

### 3. Tool Registry (v1)

**v1 status:** AISH now exposes `aish tool <name>` passthrough to the full ai_repo_tools registry. Tool set is no longer fixed.

### 4. No Real-Time Feedback During Inspect

**Behavior:** `inspect` shows start/end messages but no live progress.

**Status:** Acceptable. Full progress would require agent changes. Logs are available in agent_logs/agent_run.log.

---

## Future Compatibility Notes

### When Tools Become Modular

If Phase 2 or later adds modular tool infrastructure:
- AISH can be updated to use tool discovery/registry instead of hardcoded routes
- Usage tracking logic will remain compatible (tools still emit records to log)
- No breaking changes to command interface expected

### Adding Commands

New commands can be added to commands.py without changing AISH structure. UsageTracker already supports arbitrary command names.

---

## Running AISH v1

```bash
cd mini-codex

# List files
python -m aish map c:\path\to\repo

# machine-readable output
python -m aish --json list-tools --category evaluation

# role-scoped execution
python -m aish --as-role worker tool trust_trend --repo . 10 2

# Read a file
python -m aish read path/to/file.py

# Run inspection
python -m aish inspect --goal "analyze structure" --repo c:\path\to\repo --max-steps 5

# Self-upgrade loop
python -m aish upgrade --repo c:\path\to\repo --iterations 3

# Trust-gated orchestrator (prompts for max workers if omitted)
python -m aish orchestrate --repo c:\path\to\repo --iterations 3

# Orchestrate with explicit controls
python -m aish orchestrate --repo c:\path\to\repo --iterations 3 --trust-threshold 0.84 --max-workers 8

# Call a tool directly
python -m aish tool fast_process --repo c:\path\to\repo 5000

# Auto-route
python -m aish auto --goal "inspect architecture" --repo c:\path\to\repo

# Show usage stats
python -m aish usage
```

---

## Summary

AISH v1 is the active command layer for the mini-codex self-improving agent framework. It provides CLI access to all analysis, upgrade, and orchestration workflows, tracks usage, and gates autonomous worker scaling behind trust benchmarks. Known limitations are documented and acceptable for the v1 baseline.
