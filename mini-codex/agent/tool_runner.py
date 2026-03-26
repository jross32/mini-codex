import subprocess
import json
import os
from typing import Dict, Any, List


_AISH_AUTO_TOOLS = {
    "repo_map",
    "ai_read",
    "fast_analyze",
    "fast_process",
    "fast_prepare",
    "fast_evaluate",
    "bench_compare",
}


def _build_ai_repo_cmd(tool_script: str, tool_name: str, tool_args: List[str]) -> List[str]:
    return ["python", tool_script, tool_name, *tool_args]


def _build_aish_tool_cmd(tool_name: str, tool_args: List[str], repo_path: str) -> List[str]:
    return [
        "python",
        "-m",
        "aish",
        "--as-role",
        "worker",
        "tool",
        tool_name,
        "--repo",
        repo_path,
        *tool_args,
    ]


def run_tool(tool_name: str, tool_args: List[str], repo_path: str, use_aish_auto: bool = False) -> Dict[str, Any]:
    # All tools are invoked via ai_repo_tools/main.py as required
    # Use absolute path to ai_repo_tools since it's in the agent directory, not repo
    agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tool_script = os.path.join(agent_dir, "ai_repo_tools", "main.py")
    cmd = _build_ai_repo_cmd(tool_script, tool_name, tool_args)
    cmd_cwd = repo_path

    used_aish_auto = False
    if use_aish_auto and tool_name in _AISH_AUTO_TOOLS:
        cmd = _build_aish_tool_cmd(tool_name, tool_args, repo_path)
        # Run from mini-codex root so python -m aish can resolve module imports.
        cmd_cwd = agent_dir
        used_aish_auto = True

    try:
        completed = subprocess.run(
            cmd,
            cwd=cmd_cwd,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        if completed.returncode != 0 and used_aish_auto:
            # Bounded fallback: if AISH path fails, use direct ai_repo_tools execution.
            completed = subprocess.run(
                _build_ai_repo_cmd(tool_script, tool_name, tool_args),
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            used_aish_auto = False

        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()

        success = completed.returncode == 0
        summary = f"Tool {tool_name} finished with return code {completed.returncode}."
        evidence = stdout or stderr or "No output returned."

        # try to parse JSON suggestion if available
        suggested_next_tools = []
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict) and "suggested_next_tools" in parsed:
                suggested_next_tools = parsed["suggested_next_tools"]
        except Exception:
            suggested_next_tools = []

        warnings = []
        if not success or stderr:
            warnings.append(stderr)

        return {
            "success": success,
            "summary": summary,
            "evidence": evidence,
            "warnings": warnings,
            "suggested_next_tools": suggested_next_tools,
            "raw_stdout": stdout,
            "raw_stderr": stderr,
            "used_aish_auto": used_aish_auto,
        }

    except subprocess.TimeoutExpired as e:
        return {
            "success": False,
            "summary": f"Tool {tool_name} timed out.",
            "evidence": "",
            "warnings": [str(e)],
            "suggested_next_tools": [],
            "raw_stdout": "",
            "raw_stderr": str(e),
        }


def parse_repo_map_result(tool_result: Dict[str, Any]) -> List[str]:
    # If tool includes file listing in stdout, attempt parse; else return empty.
    output = tool_result.get("raw_stdout", "")
    files = []
    
    # Paths to exclude: dependencies, vendor, and generated directories
    # These can appear at the start or nested inside project paths (e.g., backend/.venv/)
    exclude_dirs = (
        "node_modules/",
        ".venv/",
        "venv/",
        ".env/",
        "site-packages/",
        "dist/",
        "build/",
        "__pycache__/",
        "agent_logs/",
        ".git/",
        ".egg-info/",
    )
    
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        
        # Normalize path separators for consistent checking
        normalized = line.replace("\\", "/").lower()
        
        # Skip excluded paths - check if excluded dir appears anywhere in path
        # This catches nested occurrences like backend/.venv/Lib/site-packages/...
        should_skip = False
        for excluded in exclude_dirs:
            excluded_lower = excluded.lower().rstrip("/")
            # Check both with and without directory boundaries to catch all cases
            if f"/{excluded_lower}/" in f"/{normalized}":
                should_skip = True
                break
        
        if should_skip:
            continue
        
        # Skip compiled Python files
        if normalized.endswith(".pyc"):
            continue
        
        files.append(line)

    files = sorted(files)
    return files
