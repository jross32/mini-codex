# AI Start Here

Use this sequence first for coding-assistant tasks in this repo.

1. Run ai_repo_tools before manual shell probing.
2. Use the toolkit-first order:
   - fast_analyze or repo_map for repo context
   - fast_process for next-step planning
   - fast_prepare for preflight
   - fast_evaluate for quick scoring
   - bench_compare for benchmark claims
   - env_check for dependency/setup issues
   - ai_read for file-level understanding
   - test_select for targeted read ranking
3. Fall back to manual commands only when a tool fails or lacks coverage.

## AISH auto entrypoints

- Broad auto routing: `python -m aish auto --goal "inspect and analyze" --repo <path>`
- Generic passthrough: `python -m aish tool fast_process --repo <path> 5000`
- Tool discovery: `python -m aish list-tools --category evaluation`
- Tool metadata: `python -m aish tool-info trust_trend`
- Tool validation suite: `python -m aish test-tools --tool repo_map`
- Orchestrator run: `python -m aish orchestrate --repo <path> --iterations <N>`
   - If `--max-workers` is omitted, AISH prompts for the max worker cap.
- Lifecycle list: `python -m aish list-versions trust_trend --repo <path>`
- Candidate from stable: `python -m aish create-candidate trust_trend --repo <path>`
- Hard-gated promote: `python -m aish promote-tool trust_trend --repo <path> --runs 3 --max-slowdown-pct 5`
- Usage stats: `python -m aish usage`

Generator guardrail:
- `bulk_tool_generator` is mutation-heavy and must not be run autonomously.
- Use only when explicitly user-approved and include: `--user-approved-generator`.

## Automation protocol

- Prefer `--json` for agent/worker integrations:
   - `python -m aish --json benchmark-tool fast_process --repo <path> 5000 12 1`
- Use role flags for controlled execution contexts:
   - `python -m aish --as-role worker tool trust_trend --repo <path> 20 2`
- Command contract reference:
   - `AISH_COMMAND_CONTRACT.md`

## Key locations

- Toolkit dispatcher: ai_repo_tools/main.py
- Tool modules: ai_repo_tools/tools/
- Validation bed: ai_repo_tools/validations/runner.py
- Workspace policy: .github/copilot-instructions.md
- Agent policy mirror: .github/AGENTS.md
