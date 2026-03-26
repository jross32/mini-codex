# Tool Version: V3.6 (from V3.5) | Overall improvement since last version: +0.0%
# Upgrade Summary: baseline score 3/5 -> 3/5; changes: no structural patches
import json
import os
import subprocess
import sys
import time


# Maximum characters to include in stdout/stderr excerpts
_EXCERPT_CHARS = 2000


def _infer_mode(target, repo_path):
    """
    Infer execution mode from target.
    Returns ('pytest', resolved_target) or ('python', resolved_target).
    """
    if not target:
        # No target: try pytest on the whole repo
        return "pytest", None

    lower = target.lower()

    # Explicit pytest indicators
    if lower.startswith("tests/") or lower.startswith("test_") or "test" in lower.split("/")[-1]:
        return "pytest", target

    # .py file that is not clearly a test file -> run with python
    if lower.endswith(".py"):
        return "python", target

    # Directory that looks like a test dir
    test_dir = os.path.join(repo_path, target)
    if os.path.isdir(test_dir):
        return "pytest", target

    # Fallback: treat as a pytest target (path, node id, etc.)
    return "pytest", target


def _module_name_for_python_target(target):
    """Return package module path when a target should be executed with -m."""
    if not target or not target.endswith(".py"):
        return None
    normalized = target.replace("\\", "/")
    if not normalized.startswith("ai_repo_tools/"):
        return None
    module_path = normalized[:-3].replace("/", ".")
    if not module_path:
        return None
    return module_path


def _parse_pytest_counts(stdout):
    """
    Try to extract passed/failed counts from pytest summary line.
    Returns (passed, failed) or (None, None) if not found.
    """
    passed = None
    failed = None
    for line in reversed(stdout.splitlines()):
        line_lower = line.lower()
        if "passed" in line_lower or "failed" in line_lower or "error" in line_lower:
            import re
            p = re.search(r"(\d+) passed", line_lower)
            f = re.search(r"(\d+) failed", line_lower)
            e = re.search(r"(\d+) error", line_lower)
            if p:
                passed = int(p.group(1))
            if f:
                failed = int(f.group(1))
            elif e:
                failed = int(e.group(1))
            if passed is not None or failed is not None:
                break
    return passed, failed


def cmd_run(repo_path, target=None):
    """
    Execute a test suite or script and return structured JSON results.

    Modes:
      pytest  — runs pytest on the target (or whole repo if no target)
      python  — runs python <target>

    Safety:
      - No retries
      - No auto-repair
      - No arbitrary shell execution (fixed command forms only)
      - 120-second timeout
    """
    mode, resolved_target = _infer_mode(target or "", repo_path)

    if mode == "pytest":
        cmd = [sys.executable, "-m", "pytest", "--tb=short", "-q"]
        if resolved_target:
            cmd.append(resolved_target)
    else:
        # python mode: target must exist
        script_path = os.path.join(repo_path, resolved_target)
        if not os.path.isfile(script_path):
            result = {
                "success": False,
                "mode": mode,
                "target": resolved_target,
                "error": "file_not_found",
                "returncode": 2,
                "stdout_excerpt": "",
                "stderr_excerpt": f"No such file: {resolved_target}",
                "passed_count": None,
                "failed_count": None,
                "duration_seconds": 0.0,
            }
            print(json.dumps(result))
            return 2, result

        module_name = _module_name_for_python_target(resolved_target)
        if module_name:
            # Run package files as modules so relative imports resolve.
            cmd = [sys.executable, "-m", module_name]
        else:
            cmd = [sys.executable, resolved_target]

    # Ensure tools.* imports resolve when validating ai_repo_tools modules via -m.
    env = os.environ.copy()
    ai_repo_tools_path = os.path.join(repo_path, "ai_repo_tools")
    existing_pythonpath = env.get("PYTHONPATH", "")
    if existing_pythonpath:
        env["PYTHONPATH"] = ai_repo_tools_path + os.pathsep + existing_pythonpath
    else:
        env["PYTHONPATH"] = ai_repo_tools_path

    start = time.monotonic()
    try:
        completed = subprocess.run(
            cmd,
            cwd=repo_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        elapsed = round(time.monotonic() - start, 2)
        result = {
            "success": False,
            "mode": mode,
            "target": resolved_target,
            "error": "timeout",
            "returncode": -1,
            "stdout_excerpt": "",
            "stderr_excerpt": "Command timed out after 120 seconds",
            "passed_count": None,
            "failed_count": None,
            "duration_seconds": elapsed,
        }
        print(json.dumps(result), file=sys.stderr)
        print(json.dumps(result))
        return 1, result

    elapsed = round(time.monotonic() - start, 2)
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""

    passed, failed = (None, None)
    if mode == "pytest":
        passed, failed = _parse_pytest_counts(stdout)

    success = completed.returncode == 0

    result = {
        "success": success,
        "mode": mode,
        "target": resolved_target,
        "returncode": completed.returncode,
        "stdout_excerpt": stdout[-_EXCERPT_CHARS:] if len(stdout) > _EXCERPT_CHARS else stdout,
        "stderr_excerpt": stderr[-_EXCERPT_CHARS:] if len(stderr) > _EXCERPT_CHARS else stderr,
        "passed_count": passed,
        "failed_count": failed,
        "duration_seconds": elapsed,
    }

    print(json.dumps(result))
    return 0 if success else 1, result
