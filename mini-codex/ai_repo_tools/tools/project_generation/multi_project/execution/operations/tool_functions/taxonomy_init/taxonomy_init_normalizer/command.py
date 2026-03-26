"""
taxonomy_init_normalizer - Normalize taxonomy package __init__ wrappers by preserving leaf tool exports and resetting non-leaf packages.

Category: execution
Returns: success, summary, elapsed_ms

NOTE: This tool was scaffolded by toolmaker. Implement run_taxonomy_init_normalizer() logic.
"""
import json
import re
import time
from pathlib import Path
from typing import Dict, Tuple


_EXPORT_RE = re.compile(r"^def\s+((?:cmd|run)_[A-Za-z0-9_]+)\s*\(", re.MULTILINE)
_ANY_IMPORT_EXPORT_RE = re.compile(
    r"^from\s+.+\s+import\s+((?:cmd|run)_[A-Za-z0-9_]+)\s*$", re.MULTILINE
)


def _select_leaf_export(command_py: Path) -> str:
    text = command_py.read_text(encoding="utf-8")
    names = _EXPORT_RE.findall(text)
    if not names:
        return ""
    for name in names:
        if name.startswith("cmd_"):
            return name
    return names[0]


def _normalize_nonleaf_init(init_path: Path) -> bool:
    package_name = init_path.parent.name
    desired = f"# {package_name} package.\n"
    current = init_path.read_text(encoding="utf-8")
    if current == desired:
        return False
    init_path.write_text(desired, encoding="utf-8")
    return True


def _normalize_leaf_init(init_path: Path, export_name: str) -> bool:
    desired = f"from .command import {export_name}\n"
    current = init_path.read_text(encoding="utf-8")
    if current == desired:
        return False
    init_path.write_text(desired, encoding="utf-8")
    return True


def run_taxonomy_init_normalizer(repo_path: str) -> Tuple[int, Dict]:
    """
    Normalize taxonomy package __init__ wrappers by preserving leaf tool exports and resetting non-leaf packages.

    Returns: success, summary, elapsed_ms
    """
    t0 = time.monotonic()

    tools_root = Path(repo_path) / "ai_repo_tools" / "tools"
    if not tools_root.is_dir():
        payload: Dict = {
            "success": False,
            "error": "tools_root_not_found",
            "tools_root": str(tools_root),
            "summary": "Could not locate ai_repo_tools/tools for normalization.",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }
        return 2, payload

    leaf_updated = 0
    nonleaf_updated = 0
    leaf_missing_export = 0
    leaf_wrapper_kept = 0
    scanned = 0

    for init_path in sorted(tools_root.rglob("__init__.py")):
        if "__pycache__" in init_path.parts:
            continue
        scanned += 1
        command_py = init_path.parent / "command.py"
        if command_py.is_file():
            export_name = _select_leaf_export(command_py)
            if not export_name:
                current = init_path.read_text(encoding="utf-8")
                if _ANY_IMPORT_EXPORT_RE.search(current):
                    leaf_wrapper_kept += 1
                    continue
                leaf_missing_export += 1
                continue
            if _normalize_leaf_init(init_path, export_name):
                leaf_updated += 1
            continue

        if _normalize_nonleaf_init(init_path):
            nonleaf_updated += 1

    payload: Dict = {
        "success": True,
        "taxonomy_init_normalizer_mode": "normalize_inits",
        "scanned_init_files": scanned,
        "leaf_updated": leaf_updated,
        "leaf_wrapper_kept": leaf_wrapper_kept,
        "nonleaf_updated": nonleaf_updated,
        "leaf_missing_export": leaf_missing_export,
        "summary": "Normalized taxonomy __init__.py files for leaf and non-leaf packages.",
    }

    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_taxonomy_init_normalizer(repo_path: str):
    code, payload = run_taxonomy_init_normalizer(repo_path)
    print(json.dumps(payload))
    return code, payload
