#!/usr/bin/env python3
"""
Validation bed v0 — mini-codex ai_repo_tools.

Run from mini-codex root:
  python ai_repo_tools/validations/runner.py
  python ai_repo_tools/validations/runner.py --tool ai_read
  python ai_repo_tools/validations/runner.py --case python_basic

Exits 0 if all cases pass, 1 otherwise.
"""
import argparse
import contextlib
import io
import json
import sys
import time
from pathlib import Path

# ── import path setup ─────────────────────────────────────────────────────────
_VALIDATIONS_DIR = Path(__file__).parent
_AI_REPO_TOOLS_DIR = _VALIDATIONS_DIR.parent
_MINI_CODEX_ROOT = _AI_REPO_TOOLS_DIR.parent

for _p in (str(_AI_REPO_TOOLS_DIR), str(_VALIDATIONS_DIR), str(_MINI_CODEX_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from main import dispatch_tool  # noqa: E402
import cases as _cases_mod      # noqa: E402


def _first_index(seq, target):
    try:
        return seq.index(target)
    except ValueError:
        return -1


def _run_integration_case(case):
    """Run one bounded sequence-level sentinel via RepoAgent."""
    from agent.agent_loop import run_agent

    repo = case["repo"]
    cfg = case.get("integration", {})
    goal = cfg.get("goal", "inspect code and run tests")
    max_steps = int(cfg.get("max_steps", 12))
    memory_file = cfg.get("memory_file", "agent_logs/validation_integration.log")

    t0 = time.monotonic()
    result = run_agent(goal=goal, repo_path=repo, max_steps=max_steps, memory_file=memory_file)
    duration = round(time.monotonic() - t0, 2)

    trace = result.get("trace", [])
    tools = [step.get("tool") for step in trace if isinstance(step, dict) and step.get("tool")]
    status = result.get("status")

    i_repo_map = _first_index(tools, "repo_map")
    i_ai_read = _first_index(tools, "ai_read")
    i_test_select = _first_index(tools, "test_select")
    i_cmd_run = _first_index(tools, "cmd_run")

    stage_order_ok = (
        i_repo_map != -1
        and i_ai_read != -1
        and i_test_select != -1
        and i_cmd_run != -1
        and i_repo_map < i_ai_read < i_test_select < i_cmd_run
    )
    cmd_run_seen = i_cmd_run != -1
    cmd_run_after_test_select = i_cmd_run > i_test_select if (i_cmd_run != -1 and i_test_select != -1) else False
    cmd_run_count = tools.count("cmd_run")
    # Sequence sentinel validates routing/handoff, not test pass/fail outcomes.
    # Keep a bounded threshold with a small buffer for recommendation-driven ai_read.
    no_loop_collapse = len(tools) <= (max_steps + 3) and cmd_run_count == 1

    success = bool(stage_order_ok and cmd_run_after_test_select and no_loop_collapse)
    payload = {
        "status": status,
        "trace_len": len(trace),
        "tools": tools,
        "sequence": ">".join(tools),
        "stage_order_ok": stage_order_ok,
        "cmd_run_seen": cmd_run_seen,
        "cmd_run_after_test_select": cmd_run_after_test_select,
        "cmd_run_count": cmd_run_count,
        "no_loop_collapse": no_loop_collapse,
    }
    return (0 if success else 1), payload, duration


# ── stdout suppressor ─────────────────────────────────────────────────────────
@contextlib.contextmanager
def _capture_stdout():
    """Suppress tool print() calls during validation runs."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield buf


# ── value resolver ────────────────────────────────────────────────────────────
def _resolve(payload, dotted_key):
    """
    Traverse payload (dict/list) using a dotted key.
    Supports list indexing: "recommended_files.0.file" -> payload["recommended_files"][0]["file"]
    """
    val = payload
    for part in dotted_key.split("."):
        if val is None:
            return None
        if isinstance(val, dict):
            val = val.get(part)
        elif isinstance(val, list):
            try:
                val = val[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return val


# ── condition checker ─────────────────────────────────────────────────────────
def _check_condition(actual, cond):
    """
    Check actual value against a condition spec.
    Returns (ok: bool, detail_str: str).

    Scalar cond -> exact equality.
    Dict cond supports: gte, contains, not_contains, not_none, truthy, falsy, is_none.
    """
    if isinstance(cond, dict):
        if "gte" in cond:
            ok = actual is not None and actual >= cond["gte"]
            return ok, f"{actual!r} >= {cond['gte']!r}"

        if "contains" in cond:
            if isinstance(actual, (list, dict)):
                haystack = json.dumps(actual)
            else:
                haystack = actual or ""
            ok = cond["contains"] in haystack
            return ok, f"'{cond['contains']}' in {repr(str(haystack)[:80])}"

        if "not_contains" in cond:
            if isinstance(actual, (list, dict)):
                haystack = json.dumps(actual)
            else:
                haystack = actual or ""
            ok = cond["not_contains"] not in haystack
            return ok, f"'{cond['not_contains']}' not in {repr(str(haystack)[:80])}"

        if "not_none" in cond:
            ok = actual is not None
            return ok, f"not None — got {actual!r}"

        if "truthy" in cond:
            ok = bool(actual)
            return ok, f"truthy — got {repr(actual)[:60]}"

        if "falsy" in cond:
            ok = not actual
            return ok, f"falsy — got {repr(actual)[:60]}"

        if "is_none" in cond:
            ok = actual is None
            return ok, f"is None — got {actual!r}"

        return False, f"unknown condition dict: {cond}"

    # scalar: exact match
    ok = actual == cond
    return ok, f"{actual!r} == {cond!r}"


# ── single case runner ────────────────────────────────────────────────────────
def _run_case(case):
    """
    Run one validation case.
    Returns (passed, exit_code, payload, checks, duration_s).
    checks is list of (key, ok, detail).
    """
    repo = case["repo"]
    tool = case["tool"]
    args = case.get("args", [])
    expect = case.get("expect", {})

    t0 = time.monotonic()
    try:
        if case.get("mode") == "integration":
            with _capture_stdout():
                exit_code, payload, duration = _run_integration_case(case)
        else:
            with _capture_stdout():
                exit_code, payload = dispatch_tool(repo, tool, args)
            duration = round(time.monotonic() - t0, 2)
        success_flag = exit_code == 0
    except Exception as exc:
        return False, -1, {}, [(f"dispatch raised: {exc}", False, "exception")], round(time.monotonic() - t0, 2)

    if payload is None:
        payload = {}

    checks = []
    all_pass = True

    for exp_key, exp_val in expect.items():
        if exp_key == "success":
            actual = success_flag
        elif exp_key == "exit_code":
            actual = exit_code
        elif exp_key.startswith("payload."):
            actual = _resolve(payload, exp_key[len("payload."):])
        else:
            checks.append((exp_key, False, f"unknown expect key: {exp_key!r}"))
            all_pass = False
            continue

        ok, detail = _check_condition(actual, exp_val)
        checks.append((exp_key, ok, detail))
        if not ok:
            all_pass = False

    return all_pass, exit_code, payload, checks, duration


# ── batch runner ──────────────────────────────────────────────────────────────
def run_all(filter_tool=None, filter_case=None):
    cases = _cases_mod.get_cases()
    if filter_tool:
        cases = [c for c in cases if c["tool"] == filter_tool]
    if filter_case:
        cases = [c for c in cases if c["name"] == filter_case]

    results = []
    for case in cases:
        passed, exit_code, payload, checks, duration = _run_case(case)
        results.append({
            "tool": case["tool"],
            "name": case["name"],
            "passed": passed,
            "exit_code": exit_code,
            "duration": duration,
            "checks": checks,
            "payload_keys": list(payload.keys()) if isinstance(payload, dict) else [],
        })
    return results


# ── report printer ────────────────────────────────────────────────────────────
def print_report(results, verbose=False):
    print("\n" + "=" * 72)
    print("  mini-codex validation bed v0")
    print("=" * 72)

    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"\n  [{status}]  {r['tool']:<16} {r['name']:<28}  ({r['duration']}s)")
        if not r["passed"] or verbose:
            for key, ok, detail in r["checks"]:
                marker = "  ok  " if ok else "  XX  "
                if not ok or verbose:
                    print(f"           {marker}  {key}: {detail}")

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print("\n" + "-" * 72)
    print(f"  Result: {passed}/{total} passed")
    print("=" * 72 + "\n")


# ── compact table for planning AI ─────────────────────────────────────────────
def print_table(results):
    header = f"{'tool':<16} {'case':<28} {'pass/fail':<10} {'duration':>8}"
    print("\n" + header)
    print("-" * len(header))
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"{r['tool']:<16} {r['name']:<28} {status:<10} {r['duration']:>7}s")
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print(f"\n{passed}/{total} cases passed.\n")


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="mini-codex validation bed v0")
    parser.add_argument("--tool", help="filter by tool name")
    parser.add_argument("--case", help="filter by case name")
    parser.add_argument("--verbose", action="store_true", help="show all check details")
    parser.add_argument("--table", action="store_true", help="print compact table only")
    args = parser.parse_args()

    results = run_all(filter_tool=args.tool, filter_case=args.case)

    if args.table:
        print_table(results)
    else:
        print_report(results, verbose=args.verbose)

    all_passed = all(r["passed"] for r in results)
    sys.exit(0 if all_passed else 1)
