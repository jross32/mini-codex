# Tool Version: V0.1 (from V0.0) | Overall improvement since last version: +20.0%
# Upgrade Summary: baseline score 4/5 -> 5/5; changes: added_to_dispatcher
"""tool_meta_audit - Audit per-tool metadata files for coverage and schema basics."""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple


_REQUIRED_META_KEYS = ("description", "args", "returns")


def _find_tool_dirs(tools_root: Path) -> List[Tuple[str, str, Path]]:
    discovered: List[Tuple[str, str, Path]] = []
    for category_dir in sorted(tools_root.iterdir(), key=lambda p: p.name):
        if not category_dir.is_dir() or category_dir.name.startswith("__"):
            continue

        category = category_dir.name
        for tool_dir in sorted(category_dir.iterdir(), key=lambda p: p.name):
            if not tool_dir.is_dir() or tool_dir.name.startswith("__"):
                continue
            if not (tool_dir / "command.py").is_file():
                continue
            discovered.append((category, tool_dir.name, tool_dir))

    return discovered


def run_tool_meta_audit(repo_path: str) -> Tuple[int, Dict[str, Any]]:
    t0 = time.monotonic()

    tools_root = Path(repo_path) / "ai_repo_tools" / "tools"
    if not tools_root.is_dir():
        payload = {
            "success": False,
            "error": "tools_root_not_found",
            "tools_root": str(tools_root),
            "summary": "Could not locate ai_repo_tools/tools from the provided repo path.",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }
        return 2, payload

    missing_meta: List[Dict[str, str]] = []
    invalid_meta: List[Dict[str, Any]] = []

    tool_dirs = _find_tool_dirs(tools_root)

    for category, tool_name, tool_dir in tool_dirs:
        meta_path = tool_dir / "tool.meta.json"
        if not meta_path.is_file():
            missing_meta.append(
                {
                    "category": category,
                    "tool": tool_name,
                    "meta_path": str(meta_path.relative_to(Path(repo_path))),
                }
            )
            continue

        try:
            meta_obj = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            invalid_meta.append(
                {
                    "category": category,
                    "tool": tool_name,
                    "meta_path": str(meta_path.relative_to(Path(repo_path))),
                    "error": f"invalid_json: {exc.msg} (line {exc.lineno}, col {exc.colno})",
                }
            )
            continue

        if not isinstance(meta_obj, dict):
            invalid_meta.append(
                {
                    "category": category,
                    "tool": tool_name,
                    "meta_path": str(meta_path.relative_to(Path(repo_path))),
                    "error": "invalid_shape: root must be a JSON object",
                }
            )
            continue

        missing_keys = [k for k in _REQUIRED_META_KEYS if k not in meta_obj]
        arg_errors: List[str] = []
        args_val = meta_obj.get("args")

        if "args" in meta_obj:
            if not isinstance(args_val, list):
                arg_errors.append("args must be a list")
            else:
                for idx, arg in enumerate(args_val):
                    if not isinstance(arg, dict):
                        arg_errors.append(f"args[{idx}] must be an object")
                        continue
                    if "name" not in arg or "type" not in arg:
                        arg_errors.append(f"args[{idx}] must include 'name' and 'type'")

        if missing_keys or arg_errors:
            invalid_meta.append(
                {
                    "category": category,
                    "tool": tool_name,
                    "meta_path": str(meta_path.relative_to(Path(repo_path))),
                    "missing_keys": missing_keys,
                    "arg_errors": arg_errors,
                }
            )

    all_ok = not missing_meta and not invalid_meta

    payload: Dict[str, Any] = {
        "success": True,
        "tool": "tool_meta_audit",
        "scanned_tools": len(tool_dirs),
        "missing_meta_count": len(missing_meta),
        "invalid_meta_count": len(invalid_meta),
        "all_ok": all_ok,
        "missing_meta": missing_meta,
        "invalid_meta": invalid_meta,
        "summary": (
            f"tool_meta_audit scanned {len(tool_dirs)} tools; "
            f"missing_meta={len(missing_meta)}, invalid_meta={len(invalid_meta)}"
        ),
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
    }
    return 0, payload


def cmd_tool_meta_audit(repo_path: str):
    code, payload = run_tool_meta_audit(repo_path)
    print(json.dumps(payload))
    return code, payload
