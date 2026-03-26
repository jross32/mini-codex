# Mini-Codex Repository Inventory

**Inspection Date:** March 25, 2026 (updated)  
**Repository Path:** `c:\Users\justi\Desktop\Coding Projects\mini-codex`

---

## 1. CORE CODE FILES

### 1.1 agent/ — Repository Analysis Agent Loop

**Purpose:** Core agent system that orchestrates tool invocation for code exploration

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `agent_loop.py` | ~70 | Main RepoAgent class; execution loop that runs tools sequentially | **Active** |
| `orchestrator.py` | ~310 | Trust-gated multi-worker orchestrator with autonomous spawn gating | **Active** |
| `state.py` | ~40 | AgentState dataclass; tracks tools used, files read, follow-up status | **Active** |
| `planner.py` | ~150 | Rule-based tool selection; decides which tool to run next based on state | **Active** |
| `tool_runner.py` | ~50 | Subprocess wrapper; executes tools via `ai_repo_tools/main.py` | **Active** |
| `evaluator.py` | ~30 | Simple heuristic evaluator; scores tool results (success/usefulness/uncertainty) | **Active** |
| `memory.py` | ~50 | Logging wrapper; writes step records to `agent_logs/agent_run.log` | **Active** |

**Architecture:**
- `RepoAgent(goal, repo_path, max_steps)` is the single-agent entry point
- `run_orchestrator_workflow(repo_path, ...)` runs multi-worker phases
- State progresses per single-agent: `repo_map` → `ai_read` → optionally more `ai_read` → `test_select`
- Planner uses heuristics for file selection (entry points like app.py, main.py first)
- All tool invocations logged with full state snapshots

**Orchestrator Worker Phases:**
1. `toolkit_upgrade_worker` — friction-driven toolmaker upgrades
2. `repo_inspector_worker` — architecture inspection
3. `quality_gate_worker` — deterministic lint/health checks (hard-fail gate)
4. `agent_core_upgrade_worker` — bounded agent-core policy tuning (may spawn trusted workers)

**Trust Scoring:** composite of success_rate (45%), usefulness (20%), next_step_quality (20%), self-improve readiness (10%), collaboration readiness (5%). Threshold default: 0.84.

---

### 1.2 aish/ — AISH v1 CLI Layer

**Purpose:** Lightweight command-line interface for agent/tool system

| File | Purpose | Status |
|------|---------|--------|
| `__init__.py` | Version metadata (v1.0.0) | **Active** |
| `__main__.py` | Entry point for `python -m aish` | **Active** |
| `cli.py` | Argument parsing; routes to command handlers | **Active** |
| `commands.py` | Command implementations (map, read, inspect, upgrade, orchestrate, tool, auto, usage) | **Active** |
| `usage.py` | UsageTracker class; maintains append-only JSON log at `agent_logs/aish_usage.json` | **Active** |

**Supported Commands:**
- `aish map <repo>` — List files (calls repo_map)
- `aish read <path> [--repo <path>]` — Read and summarize file
- `aish inspect --goal "..." --repo <path> [--max-steps N]` — Run full agent inspection
- `aish upgrade --repo <path> [--iterations N]` — Self-upgrade loop via toolmaker
- `aish orchestrate --repo <path> [--iterations N] [--trust-threshold F] [--max-workers N] [--unbounded]` — Trust-gated orchestrator; prompts for max-workers if omitted
- `aish tool <tool_name> --repo <path> [args...]` — Direct tool passthrough
- `aish auto [--goal "..."] [--repo <path>] [--path <file>]` — Auto-routing
- `aish usage` — Display aggregated command/tool statistics

**Current State:**
- All dead flags removed (no `--use-symbol-graph` flag)
- Clean surface, no hidden experimental wiring
- Standard paths: benchmarks via `aish inspect`; orchestration via `aish orchestrate`

---

### 1.3 ai_repo_tools/ — Tool Implementations

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `main.py` | ~250 | Tool dispatcher; implements repo_map, ai_read, test_select; dispatches to modular tools | **Active** |
| `tools/` | — | Modular tool registry with toolmaker, execution, and friction tools | **Active** |
| `tools/toolmaker/` | — | `agent_audit` and `agent_improver` tools for self-improvement | **Active** |

**Tools Implemented:**

1. **repo_map** — Repository mapping
   - Lists all Python files in repo
   - Excludes: .venv, venv, __pycache__, .git, migrations, tests, .egg-info
   - Skips ai_repo_tools directory itself

2. **ai_read** — Intelligent file reading
   - Parses Python AST to extract: imports, classes, functions
   - Returns: file size, line count, preview, extracted symbols
   - No language detection beyond Python (markdown returns preview)

3. **test_select** — Test file recommendation (stub)
   - Current: Returns JSON with empty recommendation list
   - Intended: Recommend follow-up files for agent to read
   - Signature: accepts read_files (JSON), last_read_file arguments

---

### 1.4 harness/ — Benchmark Comparison Framework

| File | Purpose | Status |
|------|---------|--------|
| `compare_v0.py` | Benchmark harness; runs baseline vs candidate on same repo | **Active** |
| `comparisons/cog_comparison.json` | Generated: cog benchmark results | **Generated** |
| `comparisons/cog_comparison.md` | Generated: cog comparison report (markdown) | **Generated** |
| `comparisons/Trade_comparison.json` | Generated: Trade benchmark results | **Generated** |
| `comparisons/Trade_comparison.md` | Generated: Trade comparison report (markdown) | **Generated** |

**Harness Design:**
- Runs same repo under two modes: "baseline" and "candidate"
- Captures: tool sequence, files read, step count
- Outputs: JSON metrics + markdown report
- Currently both modes are identical (no experimental branch)

**Recent Comparison Results:**
- `cog`: 5 steps, 3 files read (app.py, database.py, simulation.py) — IDENTICAL baseline/candidate
- `Trade`: 4 steps, 2 files read (backend/api/main.py, backend/api/__init__.py) — IDENTICAL baseline/candidate

---

## 2. DOCUMENTATION FILES

| File | Type | Purpose | Notes |
|------|------|---------|-------|
| `README.md` | .md | Repository overview and quick-start | **Current** |
| `AI_START_HERE.md` | .md | Onboarding: tool-first workflow, entrypoints | **Current** |
| `AISH_BASELINE.md` | .md | AISH v1 feature spec, command surface, architecture | **Current (v1 baseline)** |
| `AISH_ADOPTION_PLAN.md` | .md | Adoption strategy for AISH as standard interface | **Current** |
| `WORKSPACE_BASELINE.md` | .md | **MASTER BASELINE** March 25, 2026; defines what is/isn't active | **Active** |
| `BENCHMARK_REPORT.md` | .md | Test results for LifeOS_2 & cog monoliths | **Reference** |
| `BENCHMARK_RUNNER.md` | .md | Specification for benchmark test cases; expected metrics | **Specification** |
| `PROJECT_DUMP_ANALYSIS.md` | .md | Classification of all 11 projects in project_dump/ | **Reference** |
| `SYMBOL_GRAPH_PHASE2_PLAN.md` | .md | Phase 2 design for symbol_graph AST parser & integration | **Future Plan** |

**Removed docs (no longer needed):**
- `PHASE2_DECISION_GATE_BASELINE.md` — gate already passed; decisions in WORKSPACE_BASELINE
- `TEST_SELECT_INTEGRATION_REPORT.md` — one-time validation, complete
- `NF_TOOLKIT_ANALYSIS.md` — read-only analysis, no longer actionable
- `IMPORT_SELECTION_STRATEGY.md` — proposal, logic now in `planner.py`

---

## 3. LOG DIRECTORIES & RUNTIME ARTIFACTS

### 3.1 agent_logs/ — Persistent Logs

| File | Type | Purpose | Status |
|------|------|---------|--------|
| `agent_run.log` | NDJSON | Complete agent execution trace; all tool calls with state snapshots | **Growing** |
| `baseline.log` | NDJSON | Filtered agent_run entries for "baseline" repos | **Generated** |
| `candidate.log` | NDJSON | Filtered agent_run entries for "candidate" repos | **Generated** |
| `aish_usage.json` | JSON | AISH command/tool invocation tracking; append-only | **Growing** |

**Log Format Examples:**

**agent_run.log (NDJSON):**
```json
{
  "timestamp": "ISO-8601Z",
  "state": {"goal": "...", "repo_path": "...", "steps_taken": N, ...},
  "tool": "repo_map|ai_read|test_select",
  "args": [...],
  "result": {"success": bool, "summary": "...", "evidence": "..."},
  "evaluation": {"success": bool, "usefulness": 1-4, ...}
}
```

**aish_usage.json (array):**
```json
[
  {"timestamp": "ISO-8601Z", "command": "map|read|inspect|usage", "tool": "...", "success": bool},
  ...
]
```

**Notes:**
- Logs are append-only; used for analysis and troubleshooting
- `baseline.log` and `candidate.log` are derivative historical subsets
- All logs are discoverable via `aish usage` and `artifact_read`

---

## 4. GENERATED ARTIFACTS & SYMBOL GRAPHS

### 4.1 Symbol Graph Prototypes (Phase 1 Reference Only)

| File | Size | Purpose | Status |
|------|------|---------|--------|
| `symbol_graph_Trade.json` | ~20KB | AST parse of Trade repo; symbols + edges | **Reference (not wired)** |
| `symbol_graph_apaR.json` | ~50KB | AST parse of apaR repo; symbols + edges | **Reference (not wired)** |
| `symbol_graph_cog.json` | ~5KB | AST parse of cog repo; symbols + edges | **Reference (not wired)** |
| `symbol_graph_LifeOS_2.json` | ~30KB | AST parse of LifeOS_2 repo; symbols + edges | **Reference (not wired)** |
| `symbol_graph_myLife.json` | ~15KB | AST parse of myLife repo; symbols + edges | **Reference (not wired)** |

**Format:**
```json
{
  "symbols": {
    "file.py": {
      "imports": ["module.name", ...],
      "exports": ["class_A", "func_b", ...],
      "internal_calls": [{"from": "src", "to": "dst"}, ...]
    },
    ...
  },
  "edges": [
    {"source": "file1.py", "target": "file2.py", "type": "import|uses"},
    ...
  ]
}
```

**Current Status:**
- NOT wired into agent (no consumption via planner)
- Preserved for future reference
- Used only for manual inspection or Phase 2 planner integration research
- **Decision:** defer to Phase 2 pending test of value

---

## 5. STANDALONE PYTHON UTILITIES

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `symbol_graph.py` | ~150 | SymbolGraphParser class; AST-based symbol extraction | **Reference (not wired)** |

**Removed utilities (no longer needed):**
- `extract_baseline.py` — one-off log parser, not in workflow
- `log_separator.py` — one-off filter utility, not in workflow
- `project_sample.py` — 2-line stub, no purpose

---

## 6. CACHING & GENERATED DIRECTORIES

### 6.1 __pycache__/ Directories

Located in:
- `agent/__pycache__/` — Compiled .pyc files for all agent modules
- `aish/__pycache__/` — Compiled .pyc files for all aish modules

**Status:** **Auto-generated** (safe to delete, will be recreated on import)

---

## 7. EXPERIMENTAL/TEMPORARY/UNCLEAR FILES

### 7.1 Files Marked as Reference (Not Wired)

| File | Status | Notes |
|------|--------|-------|
| `symbol_graph.py` | Reference | Phase 2 candidate; not integrated |
| `symbol_graph_*.json` (all 5) | Reference artifacts | Generated by `symbol_graph.py`; not consumed by planner |

### 7.2 Generated/Side-Output Artifacts

| File | Type | Generated By | Options |
|------|------|-------------|---------|
| `harness/comparisons/cog_comparison.json` | JSON | `harness/compare_v0.py` | Can be regenerated; track in git or .gitignore |
| `harness/comparisons/cog_comparison.md` | Markdown | `harness/compare_v0.py` | Human-readable report; archive or regenerate |
| `harness/comparisons/Trade_comparison.json` | JSON | `harness/compare_v0.py` | Can be regenerated; track in git or .gitignore |
| `harness/comparisons/Trade_comparison.md` | Markdown | `harness/compare_v0.py` | Human-readable report; archive or regenerate |
| `baseline_trade.log` | Log | Manual agent run | Old baseline log; can be archived or deleted |

**Recommendation:** Add to `.gitignore` or archive in separate logs/ directory if you want to preserve history

---

## 8. DIRECTORY STRUCTURE SUMMARY

```
mini-codex/
├── agent/                              ← Core agent loop
│   ├── agent_loop.py                  (Main RepoAgent)
│   ├── state.py                       (AgentState model)
│   ├── planner.py                     (Tool selection logic)
│   ├── tool_runner.py                 (Subprocess wrapper)
│   ├── evaluator.py                   (Result scoring)
│   ├── memory.py                      (Logging)
│   └── __pycache__/                   (Auto-generated)
│
├── aish/                               ← CLI Layer (ACTIVE)
│   ├── __init__.py                    (Metadata)
│   ├── __main__.py                    (Entry point)
│   ├── cli.py                         (Argument parsing)
│   ├── commands.py                    (map, read, inspect, upgrade, orchestrate, tool, auto, usage)
│   ├── usage.py                       (UsageTracker)
│   └── __pycache__/                   (Auto-generated)
│
├── ai_repo_tools/                      ← Tool Implementations
│   ├── main.py                        (repo_map, ai_read, test_select dispatcher)
│   └── tools/                         (modular tool registry; toolmaker, execution, friction tools)
│
├── harness/                            ← Benchmark Harness
│   ├── compare_v0.py                  (Comparison runner)
│   └── comparisons/                   (Generated reports)
│       ├── cog_comparison.json
│       ├── cog_comparison.md
│       ├── Trade_comparison.json
│       └── Trade_comparison.md
│
├── agent_logs/                         ← Persistent Logs
│   ├── aish_usage.json                (AISH usage tracking)
│   ├── tool_observations.jsonl        (tool observation records)
│   ├── tool_observations_summary.json (aggregated observations)
│   └── orchestrator_summary.json      (written per orchestrate run)
│
├── [DOCUMENTATION FILES]               ← Active .md files
│   ├── README.md                      (project overview)
│   ├── AI_START_HERE.md               (onboarding)
│   ├── AISH_BASELINE.md               (v1 command spec)
│   ├── AISH_ADOPTION_PLAN.md          (adoption strategy)
│   ├── WORKSPACE_BASELINE.md           ★ MASTER BASELINE
│   ├── BENCHMARK_REPORT.md            (reference results)
│   ├── BENCHMARK_RUNNER.md            (test spec)
│   ├── PROJECT_DUMP_ANALYSIS.md       (benchmark repo classification)
│   └── SYMBOL_GRAPH_PHASE2_PLAN.md    (future plan)
│
├── [SYMBOL GRAPH PROTOTYPES]           ← Phase 1 reference only
│   ├── symbol_graph.py
│   ├── symbol_graph_Trade.json
│   ├── symbol_graph_apaR.json
│   ├── symbol_graph_cog.json
│   ├── symbol_graph_LifeOS_2.json
│   └── symbol_graph_myLife.json
│
└── [REFERENCE ARTIFACTS]
  └── symbol_graph.py                (AST parser; not wired)
```

---

## 9. KEY FINDINGS & OBSERVATIONS

### 9.1 What's Active (Production Path)

✅ **Always In Use:**
- `agent/` module — core agent loop and orchestrator
- `aish/` module — standard CLI interface
- `ai_repo_tools/main.py` + `ai_repo_tools/tools/` — tool implementations and registry
- `agent_logs/aish_usage.json` — usage tracking
- `WORKSPACE_BASELINE.md` — policy document (March 25, 2026)

### 9.2 What's Reference-Only (No Planner Integration)

❄️ **Preserved but Not Wired:**
- `symbol_graph.py` + all `symbol_graph_*.json` artifacts (Phase 2 candidates)
- `SYMBOL_GRAPH_PHASE2_PLAN.md` (future plan, not yet executed)
- `test_select` tool (stub; returns empty recommendations)

### 9.3 What Was Cleaned Up (March 25, 2026)

🗑️ **Removed:**
- `project_sample.py` (2-line stub)
- `extract_baseline.py`, `log_separator.py` (one-off utilities, not in workflow)
- `PHASE2_DECISION_GATE_BASELINE.md` (gate passed; decisions in WORKSPACE_BASELINE)
- `TEST_SELECT_INTEGRATION_REPORT.md` (one-time validation, complete)
- `NF_TOOLKIT_ANALYSIS.md` (observation-only, no longer actionable)
- `IMPORT_SELECTION_STRATEGY.md` (proposal, logic now in planner.py)
- `agent_logs/tmp_*.py`, `agent_logs/nf_bench.py` (temporary probe scripts)

### 9.4 Potential Sources of Truth Conflicts

⚠️ **Watch Out For:**
- **WORKSPACE_BASELINE.md** is the single source of truth for what's active
- If agent code deviates from WORKSPACE_BASELINE, it's likely a bug
- No dead flags should re-appear in CLI
- Phase 2 experiments should only be integrated after explicit approval and benchmark validation

---

## 10. SUMMARY TABLE

| Category | File Count | Status | Notes |
|----------|-----------|--------|-------|
| **Core Code** | 16 | ✅ Active | agent/ (incl. orchestrator), aish/, ai_repo_tools/ tools/, harness/ |
| **Documentation** | 9 | ✅ Active | Key .md files; WORKSPACE_BASELINE is master |
| **Logs** | 3 | ✅ Active | aish_usage.json, tool_observations*, orchestrator_summary |
| **Symbol Graphs** | 5 | ❄️ Reference | Phase 2 candidates; not wired to planner |
| **Reference Utilities** | 1 | 🧪 Reference | symbol_graph.py |
| **Cached** | auto | ⚙️ Auto | .pyc files; safe to delete |
| **Generated Reports** | 4 | 📊 Derivative | harness/comparisons/* |

---

## 11. ACTIONABLE INSIGHTS FOR FUTURE WORK

### What Works Well
- Clean separation: agent logic, CLI surface, tools, test harness
- All decisions documented in frozen baseline (WORKSPACE_BASELINE.md)
- Symbol graph prototype exists and ready for Phase 2 evaluation
- Append-only logs allow safe historical analysis

### What Needs Attention
- `test_select` is a stub; needs real implementation for follow-up file selection
- No formal tests for orchestrate CLI prompt path and spawn-gate benchmarks

### Next Steps (If Resuming Development)
1. **For test_select:** Implement real file recommendation logic
2. **For symbol_graph Phase 2:** Evaluate AST parser integration in planner; run benchmark comparison
3. **For orchestrate:** Add formal tests for interactive max-worker prompt and trust-gate behavior

---

**End of Inventory**
