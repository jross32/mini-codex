# AISH Command Contract (v1)

This document defines the public command surface for `python -m aish`.

## Protocol Rules

- Public interface: call `python -m aish ...`.
- Stable response shape for automation: use `--json`.
- Role-aware execution: pass `--as-role worker|orchestrator|admin|user`.
- Backward compatibility: add commands and aliases without breaking existing ones.

## Global Flags

- `--json`: emits structured output envelope.
- `--as-role <role>`: applies safety policy to role-gated commands (`tool`/`run-tool`).

## JSON Envelope

All commands support machine-readable output via `--json`.

```json
{
  "command": "tool",
  "contract": {
    "description": "Run ai_repo_tools tool through AISH",
    "args": "tool <tool_name> --repo <path> [tool args...]",
    "safety_tier": "role_gated"
  },
  "success": true,
  "exit_code": 0,
  "summary": "Command 'tool' completed successfully.",
  "caller_role": "worker",
  "stdout": "...",
  "stderr": ""
}
```

## Command Surface

- `map <repo>`
- `read <path> [--repo <path>]`
- `inspect --goal "..." --repo <path> [--max-steps N]`
- `upgrade --repo <path> [--iterations N]`
- `orchestrate --repo <path> [--iterations N] [--trust-threshold F] [--max-workers N] [--unbounded]`
- `tool <tool_name> --repo <path> [tool args...]`
- `run-tool <tool_name> --repo <path> [tool args...]`
- `validate-tool <tool_name> --repo <path>`
- `benchmark-tool <tool_name> --repo <path> [tool args...]`
- `test-tools [--tool <name>] [--case <name>] [--verbose]`
- `compare-tool <tool_name> --repo <path> --old <path> --new <path>`
- `list-tools [--category <name>]`
- `tool-info <tool_name>`
- `show-report <path> [--repo <path>]`
- `list-versions <tool_name> --repo <path>`
- `create-candidate <tool_name> --repo <path> [--candidate-id <id>]`
- `promote-tool <tool_name> --repo <path> [--candidate-id <id>] [--runs N] [--max-slowdown-pct F]`
- `auto [--goal "..."] [--repo <path>] [--path <file>] [--max-steps N]`
- `usage`

## Safety Tiers

- `worker_safe`: read/analyze/report commands.
- `orchestrator_only`: multi-step coordination commands.
- `admin_only`: sensitive mutation-heavy commands.
- `role_gated`: delegates to role-based tool policy.

Lifecycle pilot policy (`trust_trend`):
- Stable implementation is immutable during candidate evaluation.
- Promotion emits `promotion.v1` schema report under `agent_logs/`.
- Promotion requires full gate pass: correctness, performance threshold, regression shape, safety scan.

## Role Policy

- `user`: tools allowed, but `bulk_tool_generator` requires explicit approval token `--user-approved-generator`.
- `admin`: tools allowed, but `bulk_tool_generator` still requires explicit approval token `--user-approved-generator`.
- `orchestrator`: `bulk_tool_generator` is blocked.
- `worker`: restricted allowlist for safer execution; `bulk_tool_generator` is blocked.

Generator safety policy:
- Treat `bulk_tool_generator` as mutation-heavy.
- Never run it autonomously.
- Run only on explicit user request in the current conversation and with `--user-approved-generator`.

## Migration Guidance

- Use `tool`/`run-tool` for all agent-executed tool invocations where possible.
- Keep legacy direct execution only for transitional paths.
- Prefer `--json` in worker and orchestrator automation flows.
