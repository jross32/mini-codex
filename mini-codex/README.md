# mini-codex

A self-improving agent framework with tool-first orchestration.

## Quick Start

```bash
# Inspect a repository
python -m aish inspect --goal "analyze structure" --repo <path>

# Run the trust-gated orchestrator
python -m aish orchestrate --repo <path> --iterations 3

# Run a single agent inspection (auto-routing)
python -m aish auto --goal "inspect architecture" --repo <path>

# View usage stats
python -m aish usage

# Machine-readable output for automation
python -m aish --json list-tools --category evaluation

# Tool lifecycle pilot (trust_trend)
python -m aish list-versions trust_trend --repo <path>
python -m aish create-candidate trust_trend --repo <path>
python -m aish promote-tool trust_trend --repo <path> --runs 3 --max-slowdown-pct 5
```

## Live Dashboard

Start the local dashboard server:

```bash
python dashboard_v0/server.py --host 127.0.0.1 --port 8765 --repo-root .
```

Routes:

- `/mission` for the live operational dashboard and command bridge
- `/evolution` for the gamified character-growth view and narration layer

The dashboard now uses a WebSocket stream for live state updates and supports richer orchestrate controls including iterations, trust threshold, max workers, and unbounded growth.

## Commands

| Command | Purpose |
|---------|---------|
| `aish map <repo>` | List files in a repository |
| `aish read <file>` | Read and summarize a single file |
| `aish inspect --goal "..." --repo <path>` | Run full agent inspection |
| `aish upgrade --repo <path> [--iterations N]` | Run friction-driven self-upgrade loop |
| `aish orchestrate --repo <path> [--iterations N] [--trust-threshold F] [--max-workers N]` | Run trust-gated multi-worker orchestrator |
| `aish tool <tool_name> --repo <path>` | Call any ai_repo_tools tool directly |
| `aish list-tools [--category <name>]` | Discover toolkit tools by category |
| `aish tool-info <tool_name>` | Show argument and return metadata for one tool |
| `aish run-tool <tool_name> --repo <path>` | Alias for `tool` |
| `aish validate-tool <tool_name> --repo <path>` | Validate a tool command module via cmd_run |
| `aish benchmark-tool <tool_name> --repo <path>` | Benchmark tool runs (or bench_compare for fast_process) |
| `aish test-tools [--tool <name>] [--case <name>] [--verbose]` | Run automated ai_repo_tools validation cases quickly |
| `aish compare-tool <tool_name> --repo <path> --old <fileA> --new <fileB>` | Compare local artifacts/files |
| `aish show-report <path> [--repo <path>]` | Read local report/log artifact summaries |
| `aish list-versions <tool_name> --repo <path>` | Show stable/candidate/archived versions for lifecycle-managed tool |
| `aish create-candidate <tool_name> --repo <path> [--candidate-id <id>]` | Create candidate from stable without mutating live tool |
| `aish promote-tool <tool_name> --repo <path> [--candidate-id <id>] [--runs N] [--max-slowdown-pct F]` | Run hard-gated promotion and archive old stable on success |
| `aish auto --goal "..." --repo <path>` | Auto-route to map/read/inspect |
| `aish usage` | Display command and tool usage statistics |

See `AISH_COMMAND_CONTRACT.md` for safety tiers, role policy, and JSON envelope contract.

Generator safety policy:
- `bulk_tool_generator` is treated as mutation-heavy.
- Worker/orchestrator roles are blocked from using it.
- User/admin invocations require explicit approval token: `--user-approved-generator`.

Examples:
- `python -m aish test-tools --tool repo_map`
- `python -m aish tool bulk_tool_generator --repo <path> --user-approved-generator 120 1 false`

Runtime log policy is intentionally conservative in `.gitignore`: transient logs/tmp files are ignored while key JSON summaries and promotion reports remain tracked.

## Architecture

```
mini-codex/
├── aish/                   AISH CLI layer (command parsing + dispatch)
├── agent/                  Core agent loop, planner, state, evaluator
│   └── orchestrator.py     Trust-gated multi-worker orchestrator
├── ai_repo_tools/          Tool implementations (repo_map, ai_read, test_select, etc.)
│   └── tools/              Modular tool registry with toolmaker support
├── harness/                Benchmark comparison framework
├── agent_logs/             Runtime logs and orchestrator summaries
└── AI_START_HERE.md        Onboarding — start here
```

## Key Docs

- [AI_START_HERE.md](AI_START_HERE.md) — tool-first workflow and entrypoints
- [AISH_BASELINE.md](AISH_BASELINE.md) — AISH command surface and architecture
- [WORKSPACE_BASELINE.md](WORKSPACE_BASELINE.md) — current system baseline and what is/isn't active
- [REPOSITORY_INVENTORY.md](REPOSITORY_INVENTORY.md) — full file inventory with status
