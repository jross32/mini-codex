---
name: mini-codex-toolkit-workflow
description: "Execute mini-codex tasks with a toolkit-first AISH workflow. Use when planning, analyzing, validating, benchmarking, or unblocking repo tasks without ad-hoc manual fallback."
argument-hint: "Describe the task goal, scope, and whether performance claims are required"
user-invocable: true
---

# Mini-Codex Toolkit-First Workflow

## What This Skill Produces
- A deterministic execution path that prefers AISH and repo-native tools over ad-hoc shell work.
- A decision trail for when direct tool invocation is allowed.
- Completion evidence: validation status and benchmark format (when performance is discussed).

## When To Use
- You need to complete normal repo work in mini-codex.
- You are about to explore, plan, validate, or benchmark changes.
- You hit tool/environment friction and need a safe fallback path.
- You need orchestrated self-upgrade loops with worker controls.

## Inputs
- Task goal and expected output.
- Repo path.
- Whether benchmark reporting is required.
- Whether this is normal task execution or tool-maintenance work.

## Workflow
1. Classify the task.
- If the task is normal project work, use AISH as control plane.
- If the task is tool-maintenance work and AISH is insufficient, direct tool invocation is allowed.

2. Run toolkit-first sequence before manual fallback.
- Repository understanding: `fast_analyze` or `repo_map`.
- Planning: `fast_process`.
- Preflight/readiness: `fast_prepare`.
- Quick quality scoring: `fast_evaluate`.
- Benchmark claims: `bench_compare`.
- Dependency/setup failures: `env_check`.
- File reasoning: `ai_read`.
- Targeted read ranking: `test_select`.

3. Use preferred execution path.
- Broad inspect/analyze: `python -m aish auto --goal "..." --repo <path>`.
- Specific tool routing: `python -m aish tool <tool_name> --repo <path> ...`.

4. Handle blockers with repo-native remediation.
- If a required tool fails, is missing, or lacks coverage:
- Create or improve a repo-native tool.
- Use the improved tool to clear the blocker.
- Resume the original task through the toolchain.

5. Choose orchestrator mode only for bounded self-upgrade loops.
- Run: `py -m aish orchestrate --repo <path> --iterations <N>`.
- Optional controls: `--trust-threshold`, `--max-workers`, `--unbounded`.
- Worker order is fixed:
- `toolkit_upgrade_worker`.
- `repo_inspector_worker`.
- `quality_gate_worker`.
- `agent_core_upgrade_worker`.

6. Apply Python validation execution rule.
- For tools under `ai_repo_tools/`, execute as modules: `python -m <module>`.
- Prefer module execution over script-path execution when possible.

7. Apply generator safety gate.
- Never run `bulk_tool_generator` unless user explicitly requested it in this conversation.
- Require `--user-approved-generator` when it is explicitly approved.

8. Apply capability matrix checks.
- Ensure command intent matches matrix intent.
- Verify safety tier and caller role constraints.
- If docs and implementation diverge, treat implementation as source of truth and update docs/matrix.

## Decision Branches
- AISH available and sufficient:
- Use AISH path; avoid direct `ai_repo_tools/main.py` for normal tasks.
- AISH unavailable or insufficient for tool maintenance:
- Use direct invocation only for tool creation/improvement.
- Performance discussed:
- Use `bench_compare` and report baseline/current, percentage gain, multiplier, run count, bounds.
- Environment/setup failure detected:
- Run `env_check` before ad-hoc fixes.

## Completion Checks
- Command used aligns with capability matrix intent.
- Role policy and safety tier are satisfied.
- Changed tools/commands were validated via correct module path.
- Benchmark report includes required metrics when performance is claimed.
- Manual fallback (if any) includes explicit reason toolkit path was insufficient.
