"""AISH command contract and safety tiers.

Defines the stable command surface for humans, workers, and orchestrators.
"""

from typing import Dict


CALLER_ROLES = {"user", "worker", "orchestrator", "admin"}


# Explicit approval token required to run bulk tool generator mutations.
BULK_GENERATOR_APPROVAL_TOKEN = "--user-approved-generator"


COMMAND_CONTRACT: Dict[str, Dict[str, str]] = {
    "map": {
        "description": "List files in repository",
        "args": "map <repo>",
        "safety_tier": "worker_safe",
    },
    "read": {
        "description": "Read and summarize a file",
        "args": "read <path> [--repo <path>]",
        "safety_tier": "worker_safe",
    },
    "inspect": {
        "description": "Run full agent inspection",
        "args": "inspect --goal \"...\" --repo <path> [--max-steps N]",
        "safety_tier": "orchestrator_only",
    },
    "upgrade": {
        "description": "Run friction-driven self-upgrade loop",
        "args": "upgrade --repo <path> [--iterations N]",
        "safety_tier": "admin_only",
    },
    "orchestrate": {
        "description": "Run trust-gated orchestrator workflow",
        "args": "orchestrate --repo <path> [--iterations N] [--trust-threshold F] [--max-workers N] [--unbounded]",
        "safety_tier": "orchestrator_only",
    },
    "tool": {
        "description": "Run ai_repo_tools tool through AISH",
        "args": "tool <tool_name> --repo <path> [tool args...]",
        "safety_tier": "role_gated",
    },
    "run-tool": {
        "description": "Alias for tool",
        "args": "run-tool <tool_name> --repo <path> [tool args...]",
        "safety_tier": "role_gated",
    },
    "validate-tool": {
        "description": "Validate tool command module via cmd_run",
        "args": "validate-tool <tool_name> --repo <path>",
        "safety_tier": "orchestrator_only",
    },
    "benchmark-tool": {
        "description": "Benchmark a tool (bench_compare for fast_process, else timed run)",
        "args": "benchmark-tool <tool_name> --repo <path> [tool args...]",
        "safety_tier": "orchestrator_only",
    },
    "compare-tool": {
        "description": "Compare tool artifacts or files",
        "args": "compare-tool <tool_name> --repo <path> --old <path> --new <path>",
        "safety_tier": "orchestrator_only",
    },
    "list-tools": {
        "description": "List available toolkit tools",
        "args": "list-tools [--category <name>]",
        "safety_tier": "worker_safe",
    },
    "tool-info": {
        "description": "Show metadata for one toolkit tool",
        "args": "tool-info <tool_name>",
        "safety_tier": "worker_safe",
    },
    "test-tools": {
        "description": "Run automated ai_repo_tools validation cases",
        "args": "test-tools [--tool <name>] [--case <name>] [--verbose]",
        "safety_tier": "worker_safe",
    },
    "show-report": {
        "description": "Read report/log artifact summary",
        "args": "show-report <path> [--repo <path>]",
        "safety_tier": "worker_safe",
    },
    "list-versions": {
        "description": "List stable/candidate/archived versions for pilot lifecycle-managed tool",
        "args": "list-versions <tool_name> --repo <path>",
        "safety_tier": "worker_safe",
    },
    "create-candidate": {
        "description": "Create candidate from stable without touching active live version",
        "args": "create-candidate <tool_name> --repo <path> [--candidate-id <id>]",
        "safety_tier": "orchestrator_only",
    },
    "promote-tool": {
        "description": "Run hard promotion gates and promote candidate only on full pass",
        "args": "promote-tool <tool_name> --repo <path> [--candidate-id <id>] [--runs N] [--max-slowdown-pct F]",
        "safety_tier": "admin_only",
    },
    "rollback-tool": {
        "description": "Roll back a tool to a previous stable snapshot",
        "args": "rollback-tool <tool_name> --repo <path> [--to-snapshot <id>] [--reason <text>]",
        "safety_tier": "admin_only",
    },
    "deprecate-tool": {
        "description": "Mark a tool as deprecated with reason, successor, and removal date",
        "args": "deprecate-tool <tool_name> --repo <path> --reason <text> [--successor <tool>] [--removal-date <date>]",
        "safety_tier": "admin_only",
    },
    "auto": {
        "description": "Auto-route to map/read/inspect",
        "args": "auto [--goal \"...\"] [--repo <path>] [--path <file>] [--max-steps N]",
        "safety_tier": "worker_safe",
    },
    "usage": {
        "description": "Display usage stats",
        "args": "usage",
        "safety_tier": "worker_safe",
    },
}


TOOL_ROLE_POLICY = {
    "worker": {
        "allow": {
            "repo_map",
            "fast_analyze",
            "dep_graph",
            "fast_process",
            "fast_prepare",
            "fast_evaluate",
            "bench_compare",
            "diff_check",
            "task_trace",
            "friction_summarizer",
            "trust_trend",
            "git_changed_files",
            "ai_read",
            "artifact_read",
            "code_search",
            "cmd_run",
            "env_check",
            "test_select",
            "lint_check",
            "log_tail",
            "repo_health_check",
            "dep_readiness_check",
        }
    },
    "orchestrator": {
        "allow": "*",
    },
    "admin": {
        "allow": "*",
    },
    "user": {
        "allow": "*",
    },
}


def is_tool_allowed_for_role(tool_name: str, caller_role: str) -> bool:
    role = caller_role if caller_role in CALLER_ROLES else "user"

    # Mutation-heavy generator is never allowed for autonomous agent roles.
    if tool_name == "bulk_tool_generator" and role in {"worker", "orchestrator"}:
        return False

    # Dynamically registered non-toolmaker tools are worker-safe by default.
    if role == "worker":
        try:
            from tools.registry import TOOL_REGISTRY

            meta = TOOL_REGISTRY.get(tool_name)
            if meta and meta.get("category") != "toolmaker":
                return True
        except Exception:
            pass

    policy = TOOL_ROLE_POLICY.get(role, TOOL_ROLE_POLICY["user"])
    allow = policy.get("allow")
    if allow == "*":
        return True
    return tool_name in allow
