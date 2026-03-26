# Cleanup Pass v1 - March 25, 2026

## Archival Targets (Moved to this folder)

The following files should be moved from repo root to this archive:

### Phase 2 / Experimental Code
- `symbol_graph.py` - Phase 2 prototype (not integrated)
- `symbol_graph_apaR.json` - Artifact output (regenerable)
- `symbol_graph_cog.json` - Artifact output (regenerable)
- `symbol_graph_LifeOS_2.json` - Artifact output (regenerable)
- `symbol_graph_myLife.json` - Artifact output (regenerable)
- `symbol_graph_Trade.json` - Artifact output (regenerable)

### Phase 2 Planning & Decision Docs
- `SYMBOL_GRAPH_PHASE2_PLAN.md` - Future planning, gated work
- `PHASE2_DECISION_GATE_BASELINE.md` - Reference only, not active baseline

### Validated/Generated Reports (Redundant or Superseded)
- `TEST_SELECT_INTEGRATION_REPORT.md` - Detailed report; content captured in compact format
- `BENCHMARK_RUNNER.md` - Unclear purpose; utility or reference?

### Analysis/Exploration Documents (Reference Only)
- `IMPORT_SELECTION_STRATEGY.md` - Old analysis, not current source-of-truth
- `NF_TOOLKIT_ANALYSIS.md` - External toolkit research, reference only
- `PROJECT_DUMP_ANALYSIS.md` - Exploration artifact, reference only
- `REPOSITORY_INVENTORY.md` - Audit output, regenerable for future audits

### One-Off Utilities (Temporary, Not Core)
- `extract_baseline.py` - Validation helper script, one-time use
- `log_separator.py` - Validation helper script, one-time use
- `project_sample.py` - Stub file, not part of active workflow

## Deletion Candidates (Obsolete)

The following files are candidates for deletion (transient, clearly superseded):
- `baseline_trade.log` (root) - Old comparison output
- `agent_logs/baseline.log` - Obsolete; superseded by agent_run.log
- `agent_logs/candidate.log` - Obsolete; harness reports replace

## Files Intentionally Kept (Core)

- `agent/` - Core orchestration logic (6 modules)
- `aish/` - Frozen v0.1.0 CLI baseline (5 modules)
- `ai_repo_tools/` - Active tool implementations (repo_map, ai_read, test_select)
- `harness/` - Benchmark comparison framework
- `agent_logs/` - Operational logs
- `WORKSPACE_BASELINE.md` - Master baseline, source-of-truth
- `AISH_BASELINE.md` - CLI specification, reference
- `AISH_ADOPTION_PLAN.md` - Feature planning, reference
- `BENCHMARK_REPORT.md` - Validation results, reference
- `README.md` - Repo documentation

## Status

Created: March 25, 2026
Review Required: Before manual cleanup execution
Terminal Issue: PowerShell Move-Item operations could not be verified; manual cleanup steps may be required.
