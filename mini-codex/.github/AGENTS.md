# mini-codex Agent Policy

This file mirrors .github/copilot-instructions.md so both Copilot chat behavior and agent-oriented workflows follow the same toolkit-first baseline.

## Toolkit-first execution order

1. Repository understanding: run fast_analyze or repo_map first.
2. Planning next reads/actions: run fast_process first.
3. Preflight readiness: run fast_prepare first.
4. Fast triage scoring: run fast_evaluate first.
5. Performance claims: run bench_compare first.
6. Dependency/setup troubleshooting: run env_check before ad-hoc shell work.
7. File-level code understanding: run ai_read before manual parsing.
8. Targeted follow-up ranking: run test_select before random reads.

## Wall-avoidance rule

If ai_repo_tools can answer the task, use ai_repo_tools before manual fallback.
Use manual fallback only after a tool fails or does not cover the need.
When falling back, state which tool was attempted and why it was insufficient.

## Task execution constraint

- For requested work and project-building tasks, use AISH as the default and required control path.
- Do not use direct `ai_repo_tools/main.py` invocation to complete normal tasks.
- Direct tool invocation is allowed only for tool maintenance work itself (creating or improving tools) and only when the AISH path is unavailable or insufficient.
- Do not bypass the repo workflow with ad-hoc manual implementation when the task can be completed through existing repo tools.
- If an existing tool blocks progress because it fails, is missing, or lacks coverage for the needed case:
	- create a new repo-native tool or improve the existing one,
	- use that tool to overcome the blocker,
	- then continue the original task through the repo toolchain.
- Stay within what the repo agent/tool system can do unless there is no viable repo-native path.

## Tool architecture constraint (branch-first)

- Do not solve project-generation requests by writing one large single-purpose tool.
- Build or extend a branch-based tool tree with small composable tools.
- For new project/test generators, default to at least 6 functional branches (for example: intent, plan, spec, backend, frontend, validation) with leaf tools per branch.
- Keep orchestration separate from branch/leaf logic.
- Place each new tool in the appropriate taxonomy path under `ai_repo_tools/tools/`.
- It is allowed to create new parent category folders when needed for correct taxonomy and reuse.

## Benchmark reporting contract

When reporting speed or quality changes, include:
- baseline and current metrics
- percentage gain
- multiplier
- run bounds (max_files, runs, warmups)

Use bench_compare as the default benchmark path.

## Current classification

- fast_process: default-safe for planning
- fast_analyze: optional-fast-path
- fast_prepare: optional-fast-path
- fast_evaluate: optional-fast-path

## AISH auto-mode policy

- In auto mode, prefer AISH for routing-friendly calls:
	- `aish auto --goal "..." --repo <path>` for inspect-style flows.
	- `aish tool <tool_name> --repo <path> ...` for generic tool calls.
- On AISH execution failure, automatically fall back to direct ai_repo_tools dispatch.

## Orchestrator worker policy

- Use orchestrator mode for bounded self-upgrade runs:
	- `py -m aish orchestrate --repo <path> --iterations <N>` on Windows.
	- If `--max-workers` is not provided, the command prompts the user for a max worker cap at runtime.
	- Trust-gated scaling controls:
		- `--trust-threshold <float>` minimum trust score before spawning a new autonomous worker.
		- `--max-workers <N>` hard cap on total workers in a run.
		- `--unbounded` allows growth past the normal cap (still safety-capped internally).
- Worker order is fixed:
	1. `toolkit_upgrade_worker`
	2. `repo_inspector_worker`
	3. `quality_gate_worker`
	4. `agent_core_upgrade_worker`
- Quality gate is deterministic and tool-based. Preferred checks are:
	- `repo_health_check`
	- `lint_check agent/`
	- `lint_check aish/`
	- `lint_check ai_repo_tools/`
- Hard-fail workers (`toolkit_upgrade_worker`, `quality_gate_worker`, `agent_core_upgrade_worker`) may skip downstream workers on failure.

## Validation execution rule

- For Python tool files under `ai_repo_tools/`, prefer module execution (`python -m <module>`) so relative imports resolve.
- Avoid direct script-path execution for package tools when module execution is available.

## Generator safety rule

- Do not run `bulk_tool_generator` autonomously.
- It may only be run when the user explicitly requests it in the current conversation.
- When running it, include the explicit approval token: `--user-approved-generator`.
- Treat any attempt to run it without that token or without explicit user request as policy-blocked.
