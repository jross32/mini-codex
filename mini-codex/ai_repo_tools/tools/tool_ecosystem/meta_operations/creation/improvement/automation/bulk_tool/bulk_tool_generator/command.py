from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Dict, List, Tuple

from .catalog import TOOL_CATALOG, build_tool_catalog


def _wrapper_source(spec: Dict) -> str:
    name = spec["name"]
    embedded = repr(spec)
    return f'''"""{name} - {spec["description"]}."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {embedded}


def run_{name}(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_{name}(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_{name}(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
'''


def _cleanup_auto_tools(tools_root: Path) -> List[str]:
    removed: List[str] = []
    for category_dir in tools_root.iterdir():
        if not category_dir.is_dir() or category_dir.name.startswith("__"):
            continue
        for child in category_dir.iterdir():
            if child.is_dir() and child.name.startswith("auto_tool_"):
                shutil.rmtree(child)
                removed.append(f"{category_dir.name}/{child.name}")
    return removed


def _materialize_spec(tools_root: Path, spec: Dict, overwrite: bool = False) -> Tuple[bool, str]:
    category = spec["category"]
    name = spec["name"]
    tool_dir = tools_root / category / name
    command_py = tool_dir / "command.py"
    init_py = tool_dir / "__init__.py"
    meta_json = tool_dir / "tool.meta.json"

    if tool_dir.exists() and not overwrite:
        return False, name

    tool_dir.mkdir(parents=True, exist_ok=True)
    command_py.write_text(_wrapper_source(spec), encoding="utf-8")
    init_py.write_text(f"from .command import cmd_{name}\n", encoding="utf-8")
    meta_json.write_text(
        json.dumps(
            {
                "description": spec["description"],
                "args": spec["args"],
                "returns": spec["returns"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return True, name


def run_bulk_tool_generator(
    repo_path: str,
    count: int = 100,
    start_index: int = 1,
    replace_auto_tools: bool = True,
) -> Tuple[int, Dict]:
    t0 = time.monotonic()

    if count < 1:
        return 2, {"success": False, "error": "invalid_count", "detail": "count must be >= 1"}
    if start_index < 1:
        return 2, {"success": False, "error": "invalid_start_index", "detail": "start_index must be >= 1"}

    seed_catalog_size = len(TOOL_CATALOG)
    start_offset = start_index - 1
    end_offset = start_offset + count
    catalog = build_tool_catalog(end_offset)

    root = Path(repo_path)
    tools_root = root / "ai_repo_tools" / "tools"

    removed_auto_tools: List[str] = []
    if replace_auto_tools:
        removed_auto_tools = _cleanup_auto_tools(tools_root)

    generated: List[str] = []
    skipped: List[str] = []
    errors: List[str] = []

    for spec in catalog[start_offset:end_offset]:
        try:
            created, name = _materialize_spec(tools_root, spec, overwrite=True)
            if created:
                generated.append(name)
            else:
                skipped.append(name)
        except Exception as exc:
            errors.append(f"{spec['name']}: {exc}")

    elapsed_ms = round((time.monotonic() - t0) * 1000)
    success = len(errors) == 0

    payload = {
        "success": success,
        "tool": "bulk_tool_generator",
        "seed_catalog_size": seed_catalog_size,
        "materialized_catalog_size": len(catalog),
        "requested_count": count,
        "start_index": start_index,
        "generated_count": len(generated),
        "skipped_count": len(skipped),
        "removed_auto_tool_count": len(removed_auto_tools),
        "error_count": len(errors),
        "generated_tools": generated,
        "skipped_tools": skipped,
        "removed_auto_tools": removed_auto_tools,
        "errors": errors,
        "elapsed_ms": elapsed_ms,
        "summary": (
            f"Materialized {len(generated)} known tool(s) from catalog, "
            f"removed {len(removed_auto_tools)} auto tool(s), errors {len(errors)}."
        ),
    }
    return 0 if success else 1, payload


def cmd_bulk_tool_generator(
    repo_path: str,
    count: int = 100,
    start_index: int = 1,
    replace_auto_tools: bool = True,
):
    code, payload = run_bulk_tool_generator(
        repo_path,
        count=count,
        start_index=start_index,
        replace_auto_tools=replace_auto_tools,
    )
    print(json.dumps(payload))
    return code, payload
