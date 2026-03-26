"""Command implementations for AISH.

Routes CLI commands to ai_repo_tools and agent loop with optional auto behavior.
"""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add parent to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent_loop import RepoAgent
from agent.orchestrator import run_orchestrator_workflow
from aish.contract import BULK_GENERATOR_APPROVAL_TOKEN, is_tool_allowed_for_role
from aish.promotion_pipeline import (
    create_candidate,
    deprecate_tool,
    list_versions,
    rollback_tool,
    run_promotion,
)
from aish.usage import UsageTracker


_MINI_CODEX_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_AI_REPO_MAIN = os.path.join(_MINI_CODEX_ROOT, "ai_repo_tools", "main.py")
_AI_REPO_ROOT = os.path.join(_MINI_CODEX_ROOT, "ai_repo_tools")

if _AI_REPO_ROOT not in sys.path:
    sys.path.insert(0, _AI_REPO_ROOT)

try:
    from tools.registry import TOOL_CATEGORIES, TOOL_REGISTRY
except Exception:
    TOOL_CATEGORIES = {}
    TOOL_REGISTRY = {}

try:
    from tools.taxonomy import taxonomy_tool_dir
except Exception:
    taxonomy_tool_dir = None


def _run_ai_repo_tool(tool_name: str, tool_args: List[str], repo_path: str) -> Dict:
    cmd = ["python", _AI_REPO_MAIN, tool_name, *tool_args]
    completed = subprocess.run(
        cmd,
        cwd=repo_path,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    return {
        "success": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "summary": f"Tool {tool_name} finished with return code {completed.returncode}.",
    }


def _parse_payload_stdout(result: Dict) -> Dict:
    raw = result.get("stdout", "")
    if not isinstance(raw, str) or not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _record(tracker: UsageTracker, command: str, tool: str, started: float, success: bool, error: Optional[str] = None):
    duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    tracker.record_command(
        command_name=command,
        tool_used=tool,
        success=success,
        duration_ms=duration_ms,
        error=error,
    )


def _enforce_tool_invocation_policy(tool_name: str, tool_args: List[str], caller_role: str) -> Optional[str]:
    """Return policy error text when invocation should be blocked, else None."""
    if tool_name != "bulk_tool_generator":
        return None

    role = (caller_role or "user").strip().lower()
    if role in {"worker", "orchestrator"}:
        return (
            "tool 'bulk_tool_generator' is blocked for autonomous roles. "
            "Only explicit user/admin-approved invocations are allowed."
        )

    if BULK_GENERATOR_APPROVAL_TOKEN not in tool_args:
        return (
            "tool 'bulk_tool_generator' requires explicit approval token "
            f"'{BULK_GENERATOR_APPROVAL_TOKEN}'."
        )

    return None


def _prompt_max_workers(default_value: int = 16) -> int:
    """Prompt user for max worker cap when not explicitly provided."""
    # Non-interactive environments cannot answer prompts reliably.
    if not sys.stdin or not sys.stdin.isatty():
        return default_value

    while True:
        raw = input(f"Enter max workers for this orchestrator run [{default_value}]: ").strip()
        if not raw:
            return default_value
        try:
            value = int(raw)
            if value < 1:
                print("Please enter an integer >= 1.")
                continue
            return value
        except ValueError:
            print("Please enter a valid integer.")


def map_repo(repo_path: str):
    """Map files in a repository."""
    tracker = UsageTracker()
    started = time.perf_counter()

    try:
        result = _run_ai_repo_tool("repo_map", [], repo_path)
        _record(tracker, "map", "repo_map", started, result.get("success", False), result.get("stderr") or None)

        if result.get("success"):
            files = [f for f in result.get("stdout", "").split("\n") if f.strip()]
            print(f"Repository: {repo_path}")
            print(f"Files found: {len(files)}")
            print("-" * 60)
            for f in files[:50]:
                print(f"  {f}")
            if len(files) > 50:
                print(f"  ... and {len(files) - 50} more files")
            return 0

        print(f"Error: {result.get('summary', 'Unknown error')}")
        if result.get("stderr"):
            print(result.get("stderr"))
        return 1
    except Exception as exc:
        _record(tracker, "map", "repo_map", started, False, str(exc))
        print(f"Error: {str(exc)}")
        return 1


def read_file(file_path: str, repo_path: Optional[str] = None):
    """Read and summarize a file."""
    tracker = UsageTracker()
    started = time.perf_counter()
    repo_path = repo_path or os.getcwd()

    try:
        result = _run_ai_repo_tool("ai_read", [file_path], repo_path)
        _record(tracker, "read", "ai_read", started, result.get("success", False), result.get("stderr") or None)

        if result.get("success"):
            try:
                evidence = json.loads(result.get("stdout", "{}"))
            except Exception:
                evidence = {"path": file_path, "error": "Could not parse evidence"}

            print(f"File: {evidence.get('path', file_path)}")
            print(f"Lines: {evidence.get('line_count', 'unknown')}")

            imports = evidence.get("imports", [])
            if imports:
                display_imports = ", ".join(imports[:3])
                if len(imports) > 3:
                    display_imports += f" ... (+{len(imports) - 3})"
                print(f"Imports: {display_imports}")

            funcs = evidence.get("functions", [])
            if funcs:
                display_funcs = ", ".join(funcs[:3])
                if len(funcs) > 3:
                    display_funcs += f" ... (+{len(funcs) - 3})"
                print(f"Functions: {display_funcs}")

            classes = evidence.get("classes", [])
            if classes:
                display_classes = ", ".join(classes[:3])
                if len(classes) > 3:
                    display_classes += f" ... (+{len(classes) - 3})"
                print(f"Classes: {display_classes}")

            preview = evidence.get("preview", "")
            if preview:
                print("-" * 60)
                print("Preview:")
                preview_text = preview[:300]
                print(preview_text + ("..." if len(preview) > 300 else ""))

            return 0

        print(f"Error: {result.get('summary', 'Unknown error')}")
        if result.get("stderr"):
            print(result.get("stderr"))
        return 1
    except Exception as exc:
        _record(tracker, "read", "ai_read", started, False, str(exc))
        print(f"Error: {str(exc)}")
        return 1


def inspect_repo(
    goal: str,
    repo_path: str,
    max_steps: int = 10,
    toolmaker_max_iterations: int = 3,
    memory_file: str = "agent_logs/agent_run.log",
):
    """Run full agent inspection on repository."""
    tracker = UsageTracker()
    started = time.perf_counter()

    try:
        print(f"Goal: {goal}")
        print(f"Repository: {repo_path}")
        print(f"Max steps: {max_steps}")
        print("-" * 60)
        print("Starting inspection...")
        print()

        # Run the agent with AISH auto mode enabled.
        agent = RepoAgent(
            goal=goal,
            repo_path=repo_path,
            max_steps=max_steps,
            use_aish_auto=True,
            toolmaker_max_iterations=toolmaker_max_iterations,
            memory_file=memory_file,
        )
        result = agent.execute()

        success = result.get("status") in {"complete", "running"}
        _record(tracker, "inspect", "agent_loop", started, success, None if success else "agent status not complete")

        print()
        print("-" * 60)
        print("Inspection complete.")
        print(f"Full details available in {memory_file}")
        return 0 if success else 1
    except Exception as exc:
        _record(tracker, "inspect", "agent_loop", started, False, str(exc))
        print(f"Error: {str(exc)}")
        return 1


def run_tool_command(tool_name: str, repo_path: str, tool_args: List[str], caller_role: str = "user"):
    """Run any ai_repo_tools tool through AISH."""
    tracker = UsageTracker()
    started = time.perf_counter()
    command_name = f"tool:{tool_name}"

    try:
        policy_error = _enforce_tool_invocation_policy(tool_name, tool_args, caller_role)
        if policy_error:
            _record(
                tracker,
                command_name,
                tool_name,
                started,
                False,
                policy_error,
            )
            print(f"Error: {policy_error}")
            return 1

        if not is_tool_allowed_for_role(tool_name, caller_role):
            _record(
                tracker,
                command_name,
                tool_name,
                started,
                False,
                f"tool '{tool_name}' blocked for role '{caller_role}'",
            )
            print(f"Error: tool '{tool_name}' is not allowed for caller role '{caller_role}'")
            return 1

        result = _run_ai_repo_tool(tool_name, tool_args, repo_path)
        _record(tracker, command_name, tool_name, started, result.get("success", False), result.get("stderr") or None)

        if result.get("stdout"):
            print(result.get("stdout"))
        if result.get("stderr"):
            print(result.get("stderr"), file=sys.stderr)

        return 0 if result.get("success") else 1
    except Exception as exc:
        _record(tracker, command_name, tool_name, started, False, str(exc))
        print(f"Error: {str(exc)}")
        return 1


def list_tools(category: Optional[str] = None):
    """List available tools from registry, optionally filtered by category."""
    if not TOOL_REGISTRY:
        print("Error: tool registry is unavailable")
        return 1

    category_filter = (category or "").strip().lower()
    print("Available tools")
    print("-" * 60)

    total = 0
    if category_filter:
        entries = TOOL_CATEGORIES.get(category_filter)
        if not entries:
            print(f"Error: unknown category '{category_filter}'")
            return 1
        print(f"Category: {category_filter}")
        for tool_name in entries.get("tools", []):
            meta = TOOL_REGISTRY.get(tool_name, {})
            print(f"  {tool_name:24} {meta.get('description', 'no description')}")
            total += 1
    else:
        for cat, cat_meta in TOOL_CATEGORIES.items():
            print(f"{cat}:")
            for tool_name in cat_meta.get("tools", []):
                meta = TOOL_REGISTRY.get(tool_name, {})
                print(f"  {tool_name:24} {meta.get('description', 'no description')}")
                total += 1
    print("-" * 60)
    print(f"Total tools: {total}")
    return 0


def tool_info(tool_name: str):
    """Display metadata for one tool."""
    if not TOOL_REGISTRY:
        print("Error: tool registry is unavailable")
        return 1

    info = TOOL_REGISTRY.get(tool_name)
    if not info:
        print(f"Error: unknown tool '{tool_name}'")
        return 1

    print(f"Tool: {tool_name}")
    print(f"Category: {info.get('category', 'unknown')}")
    print(f"Description: {info.get('description', 'n/a')}")
    print("Args:")
    for arg in info.get("args", []):
        optional = "optional" if arg.get("optional") else "required"
        default = f", default={arg.get('default')}" if "default" in arg else ""
        print(f"  - {arg.get('name')} ({arg.get('type')}, {optional}{default})")
    print(f"Returns: {info.get('returns', 'n/a')}")
    return 0


def _resolve_tool_command_relpath(tool_name: str, repo_path: str) -> Optional[str]:
    """Resolve command.py path for a tool across shallow and taxonomy layouts."""
    repo_root = Path(repo_path).resolve()
    tools_root = repo_root / "ai_repo_tools" / "tools"

    # 1) Prefer registry-informed lookups.
    reg_meta = TOOL_REGISTRY.get(tool_name, {}) if isinstance(TOOL_REGISTRY, dict) else {}
    category = reg_meta.get("category") if isinstance(reg_meta, dict) else None
    if category:
        # 1a) Taxonomy implementation path (preferred over wrappers).
        if taxonomy_tool_dir is not None:
            taxonomy_cmd = taxonomy_tool_dir(tools_root, category, tool_name) / "command.py"
            if taxonomy_cmd.is_file():
                return str(taxonomy_cmd.relative_to(repo_root)).replace("\\", "/")

        # 1b) Legacy shallow wrapper path.
        shallow = tools_root / category / tool_name / "command.py"
        if shallow.is_file():
            return str(shallow.relative_to(repo_root)).replace("\\", "/")

    # 2) Probe all known categories via taxonomy resolver.
    if taxonomy_tool_dir is not None:
        for cat in (TOOL_CATEGORIES.keys() if TOOL_CATEGORIES else []):
            taxonomy_cmd = taxonomy_tool_dir(tools_root, cat, tool_name) / "command.py"
            if taxonomy_cmd.is_file():
                return str(taxonomy_cmd.relative_to(repo_root)).replace("\\", "/")

    # 3) Final fallback: recursive search under tools/.
    matches = sorted(
        tools_root.glob(f"**/{tool_name}/command.py"),
        key=lambda p: (len(p.parts), str(p)),
        reverse=True,
    )
    if matches:
        return str(matches[0].relative_to(repo_root)).replace("\\", "/")

    return None


def validate_tool(tool_name: str, repo_path: str):
    """Validate a tool module path via cmd_run dependency-aware execution."""
    target_rel = _resolve_tool_command_relpath(tool_name, repo_path)

    if not target_rel:
        print(f"Error: tool module not found for '{tool_name}'")
        return 1

    result = _run_ai_repo_tool("cmd_run", [target_rel], repo_path)
    if result.get("stdout"):
        print(result.get("stdout"))
    if result.get("stderr"):
        print(result.get("stderr"), file=sys.stderr)
    return 0 if result.get("success") else 1


def benchmark_tool(tool_name: str, repo_path: str, tool_args: List[str]):
    """Benchmark a tool. Uses bench_compare for fast_process; timed run otherwise."""
    started = time.perf_counter()
    if tool_name == "fast_process":
        result = _run_ai_repo_tool("bench_compare", tool_args, repo_path)
        if result.get("stdout"):
            print(result.get("stdout"))
        if result.get("stderr"):
            print(result.get("stderr"), file=sys.stderr)
        return 0 if result.get("success") else 1

    result = _run_ai_repo_tool(tool_name, tool_args, repo_path)
    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 2)
    payload = _parse_payload_stdout(result)
    print(f"Tool: {tool_name}")
    print(f"Elapsed ms: {elapsed_ms}")
    print(f"Success: {result.get('success')}")
    if payload:
        print(f"Payload keys: {', '.join(sorted(payload.keys()))}")
    if result.get("stderr"):
        print(result.get("stderr"), file=sys.stderr)
    return 0 if result.get("success") else 1


def compare_tool(tool_name: str, repo_path: str, old_ref: str, new_ref: str):
    """Compare two local artifacts/files for a tool using diff_check."""
    _ = tool_name  # tool-specific comparison can evolve later; paths are explicit today.
    result = _run_ai_repo_tool("diff_check", [old_ref, new_ref], repo_path)
    if result.get("stdout"):
        print(result.get("stdout"))
    if result.get("stderr"):
        print(result.get("stderr"), file=sys.stderr)
    return 0 if result.get("success") else 1


def show_report(report_path: str, repo_path: Optional[str] = None):
    """Show structured summary for a local report/log artifact."""
    root = repo_path or os.getcwd()
    result = _run_ai_repo_tool("artifact_read", [report_path], root)
    if result.get("stdout"):
        print(result.get("stdout"))
    if result.get("stderr"):
        print(result.get("stderr"), file=sys.stderr)
    return 0 if result.get("success") else 1


def list_tool_versions(tool_name: str, repo_path: str):
    """List stable/candidate/archived versions for pilot lifecycle-managed tools."""
    code, payload = list_versions(repo_path=repo_path, tool_name=tool_name)
    print(json.dumps(payload, indent=2))
    return 0 if code == 0 else 1


def create_tool_candidate(tool_name: str, repo_path: str, candidate_id: Optional[str] = None):
    """Create candidate version from stable without mutating active live version."""
    code, payload = create_candidate(repo_path=repo_path, tool_name=tool_name, candidate_id=candidate_id)
    print(json.dumps(payload, indent=2))
    return 0 if code == 0 else 1


def promote_tool_candidate(
    tool_name: str,
    repo_path: str,
    candidate_id: Optional[str] = None,
    runs: int = 3,
    max_slowdown_pct: float = 5.0,
):
    """Run hard-gated promotion contract on one candidate and promote only on full pass."""
    code, payload = run_promotion(
        repo_path=repo_path,
        tool_name=tool_name,
        candidate_id=candidate_id,
        runs=runs,
        max_slowdown_pct=max_slowdown_pct,
    )
    print(json.dumps(payload, indent=2))
    return 0 if code == 0 else 1


def rollback_tool_command(
    tool_name: str,
    repo_path: str,
    to_snapshot: Optional[str] = None,
    reason: str = "",
):
    """Roll back a tool to a previous stable snapshot."""
    code, payload = rollback_tool(
        repo_path=repo_path,
        tool_name=tool_name,
        to_snapshot=to_snapshot,
        reason=reason,
    )
    print(json.dumps(payload, indent=2))
    return 0 if code == 0 else 1


def deprecate_tool_command(
    tool_name: str,
    repo_path: str,
    reason: str,
    successor: Optional[str] = None,
    removal_date: Optional[str] = None,
):
    """Mark a tool as deprecated with reason, optional successor and removal date."""
    code, payload = deprecate_tool(
        repo_path=repo_path,
        tool_name=tool_name,
        reason=reason,
        successor=successor,
        removal_date=removal_date,
    )
    print(json.dumps(payload, indent=2))
    return 0 if code == 0 else 1


def auto_route(
    goal: Optional[str] = None,
    repo_path: Optional[str] = None,
    file_path: Optional[str] = None,
    max_steps: int = 10,
):
    """Auto-route to the most useful AISH command without explicit request."""
    if file_path:
        return read_file(file_path=file_path, repo_path=repo_path)

    if goal and repo_path:
        return inspect_repo(goal=goal, repo_path=repo_path, max_steps=max_steps)

    if repo_path:
        return map_repo(repo_path=repo_path)

    print("Error: auto requires at least --repo, or both --goal and --repo, or --path")
    return 1


def show_usage():
    """Display command and tool usage statistics."""
    tracker = UsageTracker()

    try:
        summary = tracker.get_summary()

        print("AISH v1 Usage Statistics")
        print("=" * 60)

        print("\nCommand Invocations:")
        print("-" * 60)
        total_commands = 0
        for command, count in sorted(summary.get("commands", {}).items()):
            total_commands += count
            print(f"  {command:24} {count:5} invocations")

        print("\nTool Usage (underlying):")
        print("-" * 60)
        total_tools = 0
        for tool, count in sorted(summary.get("tools", {}).items()):
            total_tools += count
            print(f"  {tool:24} {count:5} calls")

        print("-" * 60)
        print(f"Total commands: {total_commands}")
        print(f"Total tool calls: {total_tools}")
        print(f"Failures: {summary.get('failures', 0)}")

        durations = summary.get("durations", {})
        if durations.get("count"):
            print(f"Duration mean: {durations.get('mean_ms')} ms")
            print(f"Duration p95: {durations.get('p95_ms')} ms")

        if summary.get("timestamp"):
            print(f"\nLast updated: {summary['timestamp']}")

        return 0
    except Exception as exc:
        print(f"Error: {str(exc)}")
        return 1


def run_tool_tests(tool_name: Optional[str] = None, case_name: Optional[str] = None, verbose: bool = False):
    """Run the automated ai_repo_tools validation bed for faster tool checks."""
    cmd = ["python", os.path.join("ai_repo_tools", "validations", "runner.py")]
    if tool_name:
        cmd.extend(["--tool", tool_name])
    if case_name:
        cmd.extend(["--case", case_name])
    if verbose:
        cmd.append("--verbose")

    completed = subprocess.run(
        cmd,
        cwd=_MINI_CODEX_ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )

    if completed.stdout:
        print(completed.stdout.strip())
    if completed.stderr:
        print(completed.stderr.strip(), file=sys.stderr)

    return 0 if completed.returncode == 0 else 1


def upgrade_toolkit(repo_path: str, max_iterations: int = 3):
    """Run friction-driven multi-iteration self-upgrade loop."""
    tracker = UsageTracker()
    started = time.perf_counter()

    try:
        iters = max(1, int(max_iterations))
    except (TypeError, ValueError):
        print("Error: --iterations must be an integer")
        return 1

    # friction + initial audit + (improve/lint/validate * N) + re-audit + small buffer
    max_steps = 1 + 1 + (iters * 3) + 1 + 3
    goal = "improve toolkit with friction-driven iterative upgrades"

    code = inspect_repo(
        goal=goal,
        repo_path=repo_path,
        max_steps=max_steps,
        toolmaker_max_iterations=iters,
        memory_file="agent_logs/upgrade_run.log",
    )
    _record(tracker, "upgrade", "agent_loop", started, code == 0, None if code == 0 else "upgrade_failed")
    return code


def orchestrate_agents(
    repo_path: str,
    max_iterations: int = 3,
    trust_threshold: float = 0.84,
    max_workers: Optional[int] = None,
    allow_unbounded_growth: bool = False,
):
    """Run orchestrator + worker agents workflow for toolkit and agent-core evolution."""
    tracker = UsageTracker()
    started = time.perf_counter()

    try:
        worker_cap = max_workers if max_workers is not None else _prompt_max_workers(default_value=16)
        result = run_orchestrator_workflow(
            repo_path=repo_path,
            max_iterations=max_iterations,
            trust_threshold=trust_threshold,
            max_total_workers=worker_cap,
            allow_unbounded_growth=allow_unbounded_growth,
        )
        success = bool(result.get("success", False))
        _record(
            tracker,
            "orchestrate",
            "orchestrator",
            started,
            success,
            None if success else "orchestrator_failed",
        )

        print("Orchestrator summary")
        print("-" * 60)
        for worker in result.get("workers", []):
            benchmark = worker.get("benchmark", {})
            trust = benchmark.get("trust_score")
            trusted = benchmark.get("trusted")
            trust_text = f", trust={trust}, trusted={trusted}" if trust is not None else ""
            print(f"{worker.get('worker')}: {worker.get('status')} ({worker.get('steps')} steps{trust_text})")
        print("-" * 60)
        print(f"Workers spawned: {result.get('workers_spawned', 0)} / cap {result.get('max_total_workers')}")
        print(result.get("summary", ""))
        print("Detailed summary: agent_logs/orchestrator_summary.json")
        return 0 if success else 1
    except Exception as exc:
        _record(tracker, "orchestrate", "orchestrator", started, False, str(exc))
        print(f"Error: {str(exc)}")
        return 1
