"""Command-line interface for AISH.

Parses arguments and routes to appropriate command handler.
"""

import io
import os
import sys
from textwrap import wrap
from contextlib import redirect_stderr, redirect_stdout

from aish.contract import CALLER_ROLES, COMMAND_CONTRACT


def _render_grouped_tool_help() -> str:
    mini_codex_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ai_repo_root = os.path.join(mini_codex_root, "ai_repo_tools")
    if ai_repo_root not in sys.path:
        sys.path.insert(0, ai_repo_root)

    try:
        from tools.registry import TOOL_CATEGORIES, TOOL_REGISTRY
    except Exception:
        return ""

    lines = ["Toolkit tools by category:"]
    for category, meta in TOOL_CATEGORIES.items():
        lines.append(f"  {category} - {meta.get('description', '')}")
        for tool_name in meta.get("tools", []):
            description = TOOL_REGISTRY.get(tool_name, {}).get("description", "")
            row = f"    {tool_name}: {description}" if description else f"    {tool_name}"
            if len(row) <= 100:
                lines.append(row)
                continue
            wrapped = wrap(row.strip(), width=96)
            for idx, part in enumerate(wrapped):
                lines.append(("    " if idx == 0 else "      ") + part)
    return "\n".join(lines)


def show_help():
    """Display help message."""
    grouped_tool_help = _render_grouped_tool_help()
    help_text = """AISH v1 - Repository Analysis Command Layer

Usage:
  aish [--json] [--as-role worker|orchestrator|admin|user] <command> [args...]

Core commands:
  aish map <repo>
      List files in repository

  aish read <path> [--repo <path>]
      Read and summarize file

  aish inspect --goal "..." --repo <path> [--max-steps N]
      Run full agent inspection on repository

  aish upgrade --repo <path> [--iterations N]
      Run friction-driven self-upgrade loop (audit -> improve -> lint -> validate)

  aish orchestrate --repo <path> [--iterations N] [--trust-threshold F] [--max-workers N] [--unbounded]
      Run trust-gated orchestrator workflow; prompts for max workers if not provided

  aish tool <tool_name> --repo <path> [tool args...]
      Run any ai_repo_tools tool through AISH

Command families:
  aish list-tools [--category <name>]
      List toolkit tools by category

  aish tool-info <tool_name>
      Show args/returns metadata for one tool

  aish run-tool <tool_name> --repo <path> [tool args...]
      Alias for "tool"

      Policy: `bulk_tool_generator` is blocked for worker/orchestrator roles and
      requires explicit approval token: --user-approved-generator

  aish validate-tool <tool_name> --repo <path>
      Validate tool command module via cmd_run

  aish test-tools [--tool <name>] [--case <name>] [--verbose]
      Run automated ai_repo_tools validation cases quickly

  aish benchmark-tool <tool_name> --repo <path> [tool args...]
      Benchmark tool (bench_compare for fast_process, timed run otherwise)

  aish compare-tool <tool_name> --repo <path> --old <path> --new <path>
      Compare two local files/artifacts for the tool

  aish show-report <path> [--repo <path>]
      Read report/log artifact summary

  aish list-versions <tool_name> --repo <path>
      Show stable/candidate/archived versions for lifecycle-managed tool

  aish create-candidate <tool_name> --repo <path> [--candidate-id <id>]
      Create a candidate from stable (never mutates live tool)

  aish promote-tool <tool_name> --repo <path> [--candidate-id <id>] [--runs N] [--max-slowdown-pct F]
      Run hard promotion gates; promote only on full pass

  aish rollback-tool <tool_name> --repo <path> [--to-snapshot <id>] [--reason <text>]
      Roll back to a previous stable snapshot (admin only)

  aish deprecate-tool <tool_name> --repo <path> --reason <text> [--successor <tool>] [--removal-date <date>]
      Mark a tool as deprecated with reason and optional successor (admin only)

  aish auto [--goal "..."] [--repo <path>] [--path <file>] [--max-steps N]
      Auto-route to map/read/inspect based on available inputs

  aish usage
      Display command and tool usage statistics

Global flags:
  --json
      Emit structured JSON envelope with success/exit_code/summary/stdout/stderr

  --as-role <role>
      Apply safety tier for tool execution role (user/worker/orchestrator/admin)

Examples:
  python -m aish map c:\\path\\to\\repo
  python -m aish read path/to/file.py --repo c:\\path\\to\\repo
  python -m aish inspect --goal "analyze structure" --repo c:\\path\\to\\repo
  python -m aish upgrade --repo c:\\path\\to\\repo --iterations 3
  python -m aish orchestrate --repo c:\\path\\to\\repo --iterations 3
  python -m aish tool fast_process --repo c:\\path\\to\\repo 5000
  python -m aish list-tools --category evaluation
  python -m aish tool-info trust_trend
  python -m aish benchmark-tool fast_process --repo c:\\path\\to\\repo 5000 12 1
    python -m aish test-tools --tool repo_map
    python -m aish tool bulk_tool_generator --repo c:\\path\\to\\repo --user-approved-generator 120 1 false
  python -m aish list-versions trust_trend --repo c:\\path\\to\\repo
  python -m aish create-candidate trust_trend --repo c:\\path\\to\\repo
  python -m aish promote-tool trust_trend --repo c:\\path\\to\\repo --runs 3 --max-slowdown-pct 5
  python -m aish auto --goal "inspect architecture" --repo c:\\path\\to\\repo
  python -m aish usage --json
"""
    if grouped_tool_help:
        help_text += "\n" + grouped_tool_help + "\n"
    print(help_text)


def _extract_global_flags(args):
    output_json = False
    caller_role = "user"
    remaining = []

    i = 0
    while i < len(args):
        token = args[i]
        if token == "--json":
            output_json = True
            i += 1
            continue
        if token == "--as-role":
            if i + 1 >= len(args):
                return None, None, None, "Error: --as-role requires a value"
            value = args[i + 1].strip().lower()
            if value not in CALLER_ROLES:
                return None, None, None, f"Error: --as-role must be one of {sorted(CALLER_ROLES)}"
            caller_role = value
            i += 2
            continue

        remaining.append(token)
        i += 1

    return remaining, output_json, caller_role, None


def parse_args(args):
    """Parse command-line arguments.

    Returns: (command, kwargs, error)
    """
    normalized_args, output_json, caller_role, global_error = _extract_global_flags(args)
    if global_error:
        print(global_error)
        return None, None, None

    if not normalized_args or normalized_args[0] in ["--help", "-h", "help"]:
        show_help()
        return None, None, None

    args = normalized_args
    command = args[0]

    default_kwargs = {
        "output_json": output_json,
        "caller_role": caller_role,
    }

    if command == "map":
        if len(args) < 2:
            print("Error: map requires <repo> argument")
            return None, None, None
        payload = {"repo_path": args[1], **default_kwargs}
        return "map", payload, None

    if command == "read":
        if len(args) < 2:
            print("Error: read requires <path> argument")
            return None, None, None
        file_path = args[1]
        repo_path = os.getcwd()

        i = 2
        while i < len(args):
            if args[i] == "--repo" and i + 1 < len(args):
                repo_path = args[i + 1]
                i += 2
            else:
                print(f"Error: unknown argument {args[i]}")
                return None, None, None

        payload = {"file_path": file_path, "repo_path": repo_path, **default_kwargs}
        return "read", payload, None

    if command == "inspect":
        goal = None
        repo_path = None
        max_steps = 10

        i = 1
        while i < len(args):
            if args[i] == "--goal" and i + 1 < len(args):
                goal = args[i + 1]
                i += 2
            elif args[i] == "--repo" and i + 1 < len(args):
                repo_path = args[i + 1]
                i += 2
            elif args[i] == "--max-steps" and i + 1 < len(args):
                try:
                    max_steps = int(args[i + 1])
                except ValueError:
                    print("Error: --max-steps must be an integer")
                    return None, None, None
                i += 2
            else:
                print(f"Error: unknown argument {args[i]}")
                return None, None, None

        if not goal or not repo_path:
            print("Error: inspect requires --goal and --repo arguments")
            return None, None, None

        return "inspect", {
            "goal": goal,
            "repo_path": repo_path,
            "max_steps": max_steps,
            **default_kwargs,
        }, None

    if command == "upgrade":
        repo_path = None
        iterations = 3

        i = 1
        while i < len(args):
            if args[i] == "--repo" and i + 1 < len(args):
                repo_path = args[i + 1]
                i += 2
            elif args[i] == "--iterations" and i + 1 < len(args):
                try:
                    iterations = int(args[i + 1])
                except ValueError:
                    print("Error: --iterations must be an integer")
                    return None, None, None
                i += 2
            else:
                print(f"Error: unknown argument {args[i]}")
                return None, None, None

        if not repo_path:
            print("Error: upgrade requires --repo argument")
            return None, None, None

        return "upgrade", {
            "repo_path": repo_path,
            "max_iterations": iterations,
            **default_kwargs,
        }, None

    if command == "orchestrate":
        repo_path = None
        iterations = 3
        trust_threshold = 0.84
        max_workers = None
        unbounded = False

        i = 1
        while i < len(args):
            if args[i] == "--repo" and i + 1 < len(args):
                repo_path = args[i + 1]
                i += 2
            elif args[i] == "--iterations" and i + 1 < len(args):
                try:
                    iterations = int(args[i + 1])
                except ValueError:
                    print("Error: --iterations must be an integer")
                    return None, None, None
                i += 2
            elif args[i] == "--trust-threshold" and i + 1 < len(args):
                try:
                    trust_threshold = float(args[i + 1])
                except ValueError:
                    print("Error: --trust-threshold must be a float")
                    return None, None, None
                i += 2
            elif args[i] == "--max-workers" and i + 1 < len(args):
                try:
                    max_workers = int(args[i + 1])
                except ValueError:
                    print("Error: --max-workers must be an integer")
                    return None, None, None
                i += 2
            elif args[i] == "--unbounded":
                unbounded = True
                i += 1
            else:
                print(f"Error: unknown argument {args[i]}")
                return None, None, None

        if not repo_path:
            print("Error: orchestrate requires --repo argument")
            return None, None, None

        return "orchestrate", {
            "repo_path": repo_path,
            "max_iterations": iterations,
            "trust_threshold": trust_threshold,
            "max_workers": max_workers,
            "allow_unbounded_growth": unbounded,
            **default_kwargs,
        }, None

    if command in {"tool", "run-tool"}:
        if len(args) < 2:
            print(f"Error: {command} requires <tool_name>")
            return None, None, None

        tool_name = args[1]
        repo_path = os.getcwd()
        tool_args = []

        i = 2
        while i < len(args):
            if args[i] == "--repo" and i + 1 < len(args):
                repo_path = args[i + 1]
                i += 2
            else:
                tool_args.append(args[i])
                i += 1

        return "tool", {
            "tool_name": tool_name,
            "repo_path": repo_path,
            "tool_args": tool_args,
            "caller_role": caller_role,
            "output_json": output_json,
        }, None

    if command == "list-tools":
        category = None
        i = 1
        while i < len(args):
            if args[i] == "--category" and i + 1 < len(args):
                category = args[i + 1]
                i += 2
            else:
                print(f"Error: unknown argument {args[i]}")
                return None, None, None
        payload = {"category": category, **default_kwargs}
        return "list-tools", payload, None

    if command == "tool-info":
        if len(args) < 2:
            print("Error: tool-info requires <tool_name>")
            return None, None, None
        payload = {"tool_name": args[1], **default_kwargs}
        return "tool-info", payload, None

    if command == "validate-tool":
        if len(args) < 2:
            print("Error: validate-tool requires <tool_name>")
            return None, None, None
        tool_name = args[1]
        repo_path = os.getcwd()

        i = 2
        while i < len(args):
            if args[i] == "--repo" and i + 1 < len(args):
                repo_path = args[i + 1]
                i += 2
            else:
                print(f"Error: unknown argument {args[i]}")
                return None, None, None
        payload = {"tool_name": tool_name, "repo_path": repo_path, **default_kwargs}
        return "validate-tool", payload, None

    if command == "benchmark-tool":
        if len(args) < 2:
            print("Error: benchmark-tool requires <tool_name>")
            return None, None, None
        tool_name = args[1]
        repo_path = os.getcwd()
        tool_args = []

        i = 2
        while i < len(args):
            if args[i] == "--repo" and i + 1 < len(args):
                repo_path = args[i + 1]
                i += 2
            else:
                tool_args.append(args[i])
                i += 1

        payload = {
            "tool_name": tool_name,
            "repo_path": repo_path,
            "tool_args": tool_args,
            **default_kwargs,
        }
        return "benchmark-tool", payload, None

    if command == "test-tools":
        tool_name = None
        case_name = None
        verbose = False

        i = 1
        while i < len(args):
            if args[i] == "--tool" and i + 1 < len(args):
                tool_name = args[i + 1]
                i += 2
            elif args[i] == "--case" and i + 1 < len(args):
                case_name = args[i + 1]
                i += 2
            elif args[i] == "--verbose":
                verbose = True
                i += 1
            else:
                print(f"Error: unknown argument {args[i]}")
                return None, None, None

        payload = {
            "tool_name": tool_name,
            "case_name": case_name,
            "verbose": verbose,
            **default_kwargs,
        }
        return "test-tools", payload, None

    if command == "compare-tool":
        if len(args) < 2:
            print("Error: compare-tool requires <tool_name>")
            return None, None, None
        tool_name = args[1]
        repo_path = os.getcwd()
        old_ref = None
        new_ref = None

        i = 2
        while i < len(args):
            if args[i] == "--repo" and i + 1 < len(args):
                repo_path = args[i + 1]
                i += 2
            elif args[i] == "--old" and i + 1 < len(args):
                old_ref = args[i + 1]
                i += 2
            elif args[i] == "--new" and i + 1 < len(args):
                new_ref = args[i + 1]
                i += 2
            else:
                print(f"Error: unknown argument {args[i]}")
                return None, None, None

        if not old_ref or not new_ref:
            print("Error: compare-tool requires --old and --new")
            return None, None, None

        payload = {
            "tool_name": tool_name,
            "repo_path": repo_path,
            "old_ref": old_ref,
            "new_ref": new_ref,
            **default_kwargs,
        }
        return "compare-tool", payload, None

    if command == "show-report":
        if len(args) < 2:
            print("Error: show-report requires <path>")
            return None, None, None
        report_path = args[1]
        repo_path = os.getcwd()
        i = 2
        while i < len(args):
            if args[i] == "--repo" and i + 1 < len(args):
                repo_path = args[i + 1]
                i += 2
            else:
                print(f"Error: unknown argument {args[i]}")
                return None, None, None
        payload = {"report_path": report_path, "repo_path": repo_path, **default_kwargs}
        return "show-report", payload, None

    if command == "list-versions":
        if len(args) < 2:
            print("Error: list-versions requires <tool_name>")
            return None, None, None
        tool_name = args[1]
        repo_path = None
        i = 2
        while i < len(args):
            if args[i] == "--repo" and i + 1 < len(args):
                repo_path = args[i + 1]
                i += 2
            else:
                print(f"Error: unknown argument {args[i]}")
                return None, None, None
        if not repo_path:
            print("Error: list-versions requires --repo")
            return None, None, None
        payload = {"tool_name": tool_name, "repo_path": repo_path, **default_kwargs}
        return "list-versions", payload, None

    if command == "create-candidate":
        if len(args) < 2:
            print("Error: create-candidate requires <tool_name>")
            return None, None, None
        tool_name = args[1]
        repo_path = None
        candidate_id = None
        i = 2
        while i < len(args):
            if args[i] == "--repo" and i + 1 < len(args):
                repo_path = args[i + 1]
                i += 2
            elif args[i] == "--candidate-id" and i + 1 < len(args):
                candidate_id = args[i + 1]
                i += 2
            else:
                print(f"Error: unknown argument {args[i]}")
                return None, None, None
        if not repo_path:
            print("Error: create-candidate requires --repo")
            return None, None, None
        payload = {
            "tool_name": tool_name,
            "repo_path": repo_path,
            "candidate_id": candidate_id,
            **default_kwargs,
        }
        return "create-candidate", payload, None

    if command == "promote-tool":
        if len(args) < 2:
            print("Error: promote-tool requires <tool_name>")
            return None, None, None
        tool_name = args[1]
        repo_path = None
        candidate_id = None
        runs = 3
        max_slowdown_pct = 5.0

        i = 2
        while i < len(args):
            if args[i] == "--repo" and i + 1 < len(args):
                repo_path = args[i + 1]
                i += 2
            elif args[i] == "--candidate-id" and i + 1 < len(args):
                candidate_id = args[i + 1]
                i += 2
            elif args[i] == "--runs" and i + 1 < len(args):
                try:
                    runs = int(args[i + 1])
                except ValueError:
                    print("Error: --runs must be an integer")
                    return None, None, None
                i += 2
            elif args[i] == "--max-slowdown-pct" and i + 1 < len(args):
                try:
                    max_slowdown_pct = float(args[i + 1])
                except ValueError:
                    print("Error: --max-slowdown-pct must be a float")
                    return None, None, None
                i += 2
            else:
                print(f"Error: unknown argument {args[i]}")
                return None, None, None

        if not repo_path:
            print("Error: promote-tool requires --repo")
            return None, None, None

        payload = {
            "tool_name": tool_name,
            "repo_path": repo_path,
            "candidate_id": candidate_id,
            "runs": runs,
            "max_slowdown_pct": max_slowdown_pct,
            **default_kwargs,
        }
        return "promote-tool", payload, None

    if command == "rollback-tool":
        if len(args) < 2:
            print("Error: rollback-tool requires <tool_name>")
            return None, None, None
        tool_name = args[1]
        repo_path = None
        to_snapshot = None
        reason = ""
        i = 2
        while i < len(args):
            if args[i] == "--repo" and i + 1 < len(args):
                repo_path = args[i + 1]
                i += 2
            elif args[i] == "--to-snapshot" and i + 1 < len(args):
                to_snapshot = args[i + 1]
                i += 2
            elif args[i] == "--reason" and i + 1 < len(args):
                reason = args[i + 1]
                i += 2
            else:
                print(f"Error: unknown argument {args[i]}")
                return None, None, None
        if not repo_path:
            print("Error: rollback-tool requires --repo")
            return None, None, None
        payload = {
            "tool_name": tool_name,
            "repo_path": repo_path,
            "to_snapshot": to_snapshot,
            "reason": reason,
            **default_kwargs,
        }
        return "rollback-tool", payload, None

    if command == "deprecate-tool":
        if len(args) < 2:
            print("Error: deprecate-tool requires <tool_name>")
            return None, None, None
        tool_name = args[1]
        repo_path = None
        reason = ""
        successor = None
        removal_date = None
        i = 2
        while i < len(args):
            if args[i] == "--repo" and i + 1 < len(args):
                repo_path = args[i + 1]
                i += 2
            elif args[i] == "--reason" and i + 1 < len(args):
                reason = args[i + 1]
                i += 2
            elif args[i] == "--successor" and i + 1 < len(args):
                successor = args[i + 1]
                i += 2
            elif args[i] == "--removal-date" and i + 1 < len(args):
                removal_date = args[i + 1]
                i += 2
            else:
                print(f"Error: unknown argument {args[i]}")
                return None, None, None
        if not repo_path:
            print("Error: deprecate-tool requires --repo")
            return None, None, None
        if not reason:
            print("Error: deprecate-tool requires --reason")
            return None, None, None
        payload = {
            "tool_name": tool_name,
            "repo_path": repo_path,
            "reason": reason,
            "successor": successor,
            "removal_date": removal_date,
            **default_kwargs,
        }
        return "deprecate-tool", payload, None

    if command == "auto":
        goal = None
        repo_path = None
        file_path = None
        max_steps = 10

        i = 1
        while i < len(args):
            if args[i] == "--goal" and i + 1 < len(args):
                goal = args[i + 1]
                i += 2
            elif args[i] == "--repo" and i + 1 < len(args):
                repo_path = args[i + 1]
                i += 2
            elif args[i] == "--path" and i + 1 < len(args):
                file_path = args[i + 1]
                i += 2
            elif args[i] == "--max-steps" and i + 1 < len(args):
                try:
                    max_steps = int(args[i + 1])
                except ValueError:
                    print("Error: --max-steps must be an integer")
                    return None, None, None
                i += 2
            else:
                print(f"Error: unknown argument {args[i]}")
                return None, None, None

        return "auto", {
            "goal": goal,
            "repo_path": repo_path,
            "file_path": file_path,
            "max_steps": max_steps,
            **default_kwargs,
        }, None

    if command == "usage":
        return "usage", default_kwargs, None

    print(f"Error: unknown command '{command}'")
    show_help()
    return None, None, None


def dispatch(command, kwargs):
    """Dispatch to appropriate command handler."""
    from aish import commands

    try:
        if command == "map":
            return commands.map_repo(kwargs["repo_path"])
        if command == "read":
            return commands.read_file(kwargs["file_path"], kwargs.get("repo_path"))
        if command == "inspect":
            return commands.inspect_repo(
                kwargs["goal"],
                kwargs["repo_path"],
                kwargs.get("max_steps", 10),
            )
        if command == "upgrade":
            return commands.upgrade_toolkit(
                kwargs["repo_path"],
                kwargs.get("max_iterations", 3),
            )
        if command == "orchestrate":
            return commands.orchestrate_agents(
                kwargs["repo_path"],
                kwargs.get("max_iterations", 3),
                kwargs.get("trust_threshold", 0.84),
                kwargs.get("max_workers", 16),
                kwargs.get("allow_unbounded_growth", False),
            )
        if command == "tool":
            return commands.run_tool_command(
                kwargs["tool_name"],
                kwargs["repo_path"],
                kwargs.get("tool_args", []),
                kwargs.get("caller_role", "user"),
            )
        if command == "list-tools":
            return commands.list_tools(kwargs.get("category"))
        if command == "tool-info":
            return commands.tool_info(kwargs["tool_name"])
        if command == "validate-tool":
            return commands.validate_tool(kwargs["tool_name"], kwargs["repo_path"])
        if command == "benchmark-tool":
            return commands.benchmark_tool(
                kwargs["tool_name"],
                kwargs["repo_path"],
                kwargs.get("tool_args", []),
            )
        if command == "test-tools":
            return commands.run_tool_tests(
                tool_name=kwargs.get("tool_name"),
                case_name=kwargs.get("case_name"),
                verbose=kwargs.get("verbose", False),
            )
        if command == "compare-tool":
            return commands.compare_tool(
                kwargs["tool_name"],
                kwargs["repo_path"],
                kwargs["old_ref"],
                kwargs["new_ref"],
            )
        if command == "show-report":
            return commands.show_report(kwargs["report_path"], kwargs.get("repo_path"))
        if command == "list-versions":
            return commands.list_tool_versions(kwargs["tool_name"], kwargs["repo_path"])
        if command == "create-candidate":
            return commands.create_tool_candidate(
                kwargs["tool_name"],
                kwargs["repo_path"],
                kwargs.get("candidate_id"),
            )
        if command == "promote-tool":
            return commands.promote_tool_candidate(
                kwargs["tool_name"],
                kwargs["repo_path"],
                kwargs.get("candidate_id"),
                kwargs.get("runs", 3),
                kwargs.get("max_slowdown_pct", 5.0),
            )
        if command == "rollback-tool":
            return commands.rollback_tool_command(
                kwargs["tool_name"],
                kwargs["repo_path"],
                kwargs.get("to_snapshot"),
                kwargs.get("reason", ""),
            )
        if command == "deprecate-tool":
            return commands.deprecate_tool_command(
                kwargs["tool_name"],
                kwargs["repo_path"],
                kwargs["reason"],
                kwargs.get("successor"),
                kwargs.get("removal_date"),
            )
        if command == "auto":
            return commands.auto_route(
                goal=kwargs.get("goal"),
                repo_path=kwargs.get("repo_path"),
                file_path=kwargs.get("file_path"),
                max_steps=kwargs.get("max_steps", 10),
            )
        if command == "usage":
            return commands.show_usage()
    except Exception as exc:
        print(f"Error: {str(exc)}")
        import traceback
        traceback.print_exc()
        return 1

    return 1


def _summary_for_exit(command, exit_code):
    if exit_code == 0:
        return f"Command '{command}' completed successfully."
    return f"Command '{command}' failed with exit code {exit_code}."


def _is_command_allowed(command, caller_role):
    role = (caller_role or "user").lower()
    tier = COMMAND_CONTRACT.get(command, {}).get("safety_tier", "worker_safe")
    if role in {"user", "admin"}:
        return True
    if role == "orchestrator":
        return tier != "admin_only"
    if role == "worker":
        return tier in {"worker_safe", "role_gated"}
    return True


def _emit_json_envelope(command, kwargs, exit_code, stdout_text, stderr_text):
    import json

    output = {
        "command": command,
        "contract": COMMAND_CONTRACT.get(command, {}),
        "success": exit_code == 0,
        "exit_code": int(exit_code),
        "summary": _summary_for_exit(command, exit_code),
        "caller_role": kwargs.get("caller_role", "user"),
        "stdout": stdout_text.strip(),
        "stderr": stderr_text.strip(),
    }
    print(json.dumps(output, indent=2))


def main():
    """Main CLI entry point."""
    args = sys.argv[1:]
    command, kwargs, error = parse_args(args)

    if error:
        return 1

    if command is None:
        return 0

    if not _is_command_allowed(command, kwargs.get("caller_role", "user")):
        message = (
            f"Error: command '{command}' is not allowed for caller role "
            f"'{kwargs.get('caller_role', 'user')}'"
        )
        if kwargs.get("output_json"):
            _emit_json_envelope(
                command=command,
                kwargs=kwargs,
                exit_code=1,
                stdout_text=message,
                stderr_text="",
            )
            return 1
        print(message)
        return 1

    if kwargs.get("output_json"):
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            exit_code = dispatch(command, kwargs) or 0
        _emit_json_envelope(
            command=command,
            kwargs=kwargs,
            exit_code=exit_code,
            stdout_text=stdout_buffer.getvalue(),
            stderr_text=stderr_buffer.getvalue(),
        )
        return exit_code

    return dispatch(command, kwargs) or 0
