# mini-codex Toolkit-First Instructions

This workspace is toolkit-first by default.

## Mandatory sequence before manual fallback

1. For repository understanding tasks, run `fast_analyze` or `repo_map` first.
2. For next-step planning tasks, run `fast_process` first.
3. For preflight/readiness tasks, run `fast_prepare` first.
4. For quick quality scoring tasks, run `fast_evaluate` first.
5. For benchmark claims, run `bench_compare` first.
6. For dependency/setup failures, run `env_check` before ad-hoc commands.
7. For file reasoning tasks, run `ai_read` before manual parsing.
8. For targeted read ranking, run `test_select` before random reads.

## Wall-avoidance rule

If a task can be answered by ai_repo_tools, do not use manual shell probing first.
Only use manual fallback when a tool explicitly fails or lacks coverage.
When falling back, state why the toolkit path was insufficient.

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

## Benchmark reporting rule

When performance is discussed, include:
- baseline and current metrics
- percentage gain
- multiplier
- run count and bounds (max_files, warmups)

Use `bench_compare` for this by default.

## Preferred defaults

- `fast_process` is default-safe for planning.
- `fast_analyze`, `fast_prepare`, and `fast_evaluate` are optional-fast-path helpers unless evidence upgrades them.

## AISH auto-mode policy

- Use AISH automatically when it adds routing value:
	- `python -m aish auto --goal "..." --repo <path>` for broad inspect/analyze auto flows.
	- `python -m aish tool <tool_name> --repo <path> ...` for generic tool passthrough.
- If AISH path fails, fall back to direct `ai_repo_tools/main.py` invocation and continue.

## Orchestrator worker policy

- Use orchestrator mode for bounded self-upgrade loops:
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

- When validating Python tool files under `ai_repo_tools/`, run them as modules (`python -m <module>`) so relative imports resolve correctly.
- Avoid direct script-path execution for package tools when module execution is available.

## Generator safety rule

- Do not run `bulk_tool_generator` autonomously.
- It may only be run when the user explicitly requests it in the current conversation.
- When running it, include the explicit approval token: `--user-approved-generator`.
- Treat any attempt to run it without that token or without explicit user request as policy-blocked.

## Capability matrix default and enforcement

- Default to AISH as the control plane and ai_repo_tools as the execution plane.
- Use AISH commands for normal task execution; do not use direct tool invocation for normal tasks.
- Direct tool invocation is reserved for tool creation/improvement maintenance when AISH is unavailable or insufficient.
- Always maintain and consult a command
-to-tool capability matrix for execution decisions.

Required matrix fields:
- command
- underlying tool/runtime
- mode (direct, agent, orchestrated, router)
- safety tier
- allowed caller roles
- mutates state (yes/no)
- required guardrails/approval flags
- validation path
- benchmark path

If matrix and implementation differ, implementation is source of truth and the matrix must be updated immediately.

## Command/tool mismatch fixes (must be enforced)

1. Validation path normalization
- Validation must support taxonomy-based module paths in addition to shallow category paths.
- Prefer module execution (`python -m <module>`) for tool validation when resolvable.
- Do not rely only on `ai_repo_tools/tools/<category>/<tool>/command.py` lookup.

2. Benchmark behavior normalization
- `benchmark-tool` must report benchmark mode clearly for all tools.
- For full comparisons, report baseline, current, percentage delta, multiplier, run count, and warmups.
- If full comparison is unavailable, explicitly mark timed-only mode with reason.

3. compare-tool semantic clarity
- `compare-tool` must be either tool-aware or explicitly documented as generic artifact/file diff.
- Do not keep undocumented tool-specific parameters that are ignored.

4. Role policy transparency
- Worker role behavior for dynamically registered non-toolmaker tools must be explicit in docs and policy checks.
- `bulk_tool_generator` remains blocked for `worker` and `orchestrator` roles.
- `user` and `admin` invocations of `bulk_tool_generator` require `--user-approved-generator`.

5. Dispatch consistency
- Keep static dispatch and dynamic registry fallback behavior aligned.
- Newly registered tools must be documented as dynamic-only or added to explicit command paths when required by policy/testing.

## Default execution guardrails

- Default toolkit-first sequence:
	- `fast_analyze` or `repo_map`
	- `fast_process`
	- `fast_prepare`
	- `fast_evaluate`
	- `bench_compare` (for benchmark claims)
	- `env_check` (for dependency/setup failures)
	- `ai_read`
	- `test_select`
- Prefer `python -m aish auto --goal "..." --repo <path>` for broad inspect/analyze flows.
- Prefer `python -m aish tool <tool_name> --repo <path> ...` for direct tool passthrough with policy controls.
- Avoid direct `ai_repo_tools/main.py` task execution except for tool maintenance exceptions defined above.

## Completion gate

Before declaring work complete, verify:
- command used matches capability matrix intent
- safety tier and role policy are satisfied
- validation path was executed for changed tools/commands
- benchmark reporting format is complete when performance is discussed
