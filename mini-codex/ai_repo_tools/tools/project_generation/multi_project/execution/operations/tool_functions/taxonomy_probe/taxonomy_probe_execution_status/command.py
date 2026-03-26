"""
taxonomy_probe_execution_status - Report taxonomy routing/probe status and basic package health checks.

Category: execution
Returns: success, summary, elapsed_ms

NOTE: This tool was scaffolded by toolmaker. Implement run_taxonomy_probe_execution_status() logic.
"""
import json
import re
import time
from pathlib import Path
from typing import Dict, Tuple


_BAD_NONLEAF_RE = re.compile(
    r"^from\s+\.command\s+import\s+(?:cmd|run)_[A-Za-z0-9_]+\s*$", re.MULTILINE
)
_BAD_ABS_RE = re.compile(r"^from\s+tools\.", re.MULTILINE)
_BAD_REG_RE = re.compile(
    r"from\s+\.registry\s+import\s+TOOL_CATEGORIES\s*,\s*TOOL_REGISTRY", re.MULTILINE
)
_LEAF_EXPORT_RE = re.compile(
    r"^from\s+\.command\s+import\s+(?:cmd|run)_[A-Za-z0-9_]+\s*$", re.MULTILINE
)
_LEAF_FORWARD_RE = re.compile(
    r"^from\s+tools\.[A-Za-z0-9_\.]+\s+import\s+(?:cmd|run)_[A-Za-z0-9_]+\s*$", re.MULTILINE
)


def run_taxonomy_probe_execution_status(repo_path: str) -> Tuple[int, Dict]:
    """
    Report taxonomy routing/probe status and basic package health checks.

    Returns: success, summary, elapsed_ms
    """
    t0 = time.monotonic()

    root = Path(repo_path)
    tools_root = root / "ai_repo_tools" / "tools"
    if not tools_root.is_dir():
        payload: Dict = {
            "success": False,
            "error": "tools_root_not_found",
            "tools_root": str(tools_root),
            "summary": "Could not locate ai_repo_tools/tools for taxonomy probe status.",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }
        return 2, payload

    total = 0
    leaf_ok = 0
    leaf_bad = []
    nonleaf_bad = []

    for init_path in sorted(tools_root.rglob("__init__.py")):
        if "__pycache__" in init_path.parts:
            continue
        total += 1
        text = init_path.read_text(encoding="utf-8")
        is_leaf = (init_path.parent / "command.py").is_file()

        if is_leaf:
            stripped = text.strip()
            if _LEAF_EXPORT_RE.fullmatch(stripped) or _LEAF_FORWARD_RE.fullmatch(stripped):
                leaf_ok += 1
            else:
                leaf_bad.append(str(init_path.relative_to(root)))
            continue

        if _BAD_NONLEAF_RE.search(text) or _BAD_ABS_RE.search(text) or _BAD_REG_RE.search(text):
            nonleaf_bad.append(str(init_path.relative_to(root)))

    probe_tool = (
        tools_root
        / "project_generation"
        / "multi_project"
        / "execution"
        / "operations"
        / "tool_functions"
        / "taxonomy_probe"
        / "taxonomy_probe_execution"
        / "command.py"
    )

    healthy = len(leaf_bad) == 0 and len(nonleaf_bad) == 0 and probe_tool.is_file()
    payload: Dict = {
        "success": healthy,
        "taxonomy_probe_execution_status_mode": "package_health_scan",
        "total_init_files": total,
        "leaf_ok": leaf_ok,
        "leaf_bad_count": len(leaf_bad),
        "nonleaf_bad_count": len(nonleaf_bad),
        "probe_tool_present": probe_tool.is_file(),
        "leaf_bad_samples": leaf_bad[:20],
        "nonleaf_bad_samples": nonleaf_bad[:20],
        "summary": (
            "Taxonomy package health is clean."
            if healthy
            else "Taxonomy package health has issues; run taxonomy_init_normalizer."
        ),
    }

    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_taxonomy_probe_execution_status(repo_path: str):
    code, payload = run_taxonomy_probe_execution_status(repo_path)
    print(json.dumps(payload))
    return code, payload
