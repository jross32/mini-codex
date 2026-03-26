"""
tool_improver - Apply deterministic improvements to an existing tool in-place.

Given a tool name, this tool:
  1. Locates the tool's command.py (via registry or filesystem scan)
  2. Audits which quality dimensions are missing (same checks as tool_audit)
  3. Applies SAFE patches first (no code changes):
       - Adds tool to registry.py if missing
       - Adds tool to category __init__.py if missing
       - Adds tool to main.py dispatcher if missing
       - Adds a basic validation case to validations/cases.py if missing
  4. Applies CODE patches to command.py if safe:
       - Adds elapsed_ms timing via time.monotonic()
       - Adds "summary" key to return payload via payload.setdefault()
       - Compile-checks the result; reverts on failure
  5. Returns a structured report of all patches applied and files modified.

This is the core of the self-improvement loop. Tools are improved IN-PLACE —
no version files, no clutter. The improvement history lives in agent_logs/.
"""
import ast
import json
import os
import py_compile
import re
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tools.taxonomy import taxonomy_tool_dir

_AI_REPO_TOOLS = Path(__file__).resolve().parents[3]
_TOOLS_DIR = _AI_REPO_TOOLS / "tools"
_MAIN_PY = _AI_REPO_TOOLS / "main.py"
_REGISTRY = _TOOLS_DIR / "registry.py"
_CASES_PY = _AI_REPO_TOOLS / "validations" / "cases.py"
_STATE_JSON = _AI_REPO_TOOLS / "agent_logs" / "toolmaker_state.json"

_CATEGORY_DIRS = [
    "discovery", "planning", "evaluation", "reading",
    "execution", "health", "toolmaker", "game_systems",
]

_DISPATCHER_TEMPLATE = '''\
    if tool_name == "{name}":
        target = tool_args[0] if tool_args else None
        return cmd_{name}(repo_path, target)\n'''

_VALIDATION_TEMPLATE = '''\
        {{
            "name": "{name}_basic",
            "tool": "{name}",
            "repo": mc,
            "args": [],
            "expect": {{
                "success": True,
                "payload.summary": {{"not_none": True}},
            }},
        }},\n'''


# ── helpers ──────────────────────────────────────────────────────────────────

def _read_safe(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, OSError):
            continue
    return ""


def _write_safe(path: Path, content: str) -> bool:
    try:
        path.write_text(content, encoding="utf-8")
        return True
    except OSError:
        return False


def _load_toolmaker_state() -> Dict:
    if not _STATE_JSON.exists():
        return {"levels": {}, "history": []}
    try:
        data = json.loads(_STATE_JSON.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"levels": {}, "history": []}
        data.setdefault("levels", {})
        data.setdefault("history", [])
        if not isinstance(data["levels"], dict):
            data["levels"] = {}
        if not isinstance(data["history"], list):
            data["history"] = []
        return data
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"levels": {}, "history": []}


def _save_toolmaker_state(state: Dict) -> bool:
    try:
        _STATE_JSON.parent.mkdir(parents=True, exist_ok=True)
        _STATE_JSON.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


def _bump_upgrade_level(tool_name: str, category: str, patches_applied: List[str], warnings: List[str]) -> Tuple[int, int, bool]:
    """Increment and persist per-tool upgrade level; returns (before, after, saved)."""
    state = _load_toolmaker_state()
    levels = state.get("levels", {})
    before = int(levels.get(tool_name, 0) or 0)
    after = before + 1
    levels[tool_name] = after
    state["levels"] = levels

    history = state.get("history", [])
    history.append(
        {
            "tool": tool_name,
            "category": category,
            "upgrade_level": after,
            "patch_count": len(patches_applied),
            "patches": list(patches_applied),
            "warnings": list(warnings),
            "ts_epoch": int(time.time()),
        }
    )
    # Keep the file bounded.
    if len(history) > 400:
        history = history[-400:]
    state["history"] = history
    saved = _save_toolmaker_state(state)
    return before, after, saved


def _compile_check(content: str) -> Optional[str]:
    """Return None if content compiles OK, else error string."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as f:
        f.write(content)
        tmp = f.name
    try:
        py_compile.compile(tmp, doraise=True)
        return None
    except py_compile.PyCompileError as exc:
        return str(exc)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def _find_tool(tool_name: str) -> Optional[Tuple[str, Path]]:
    """Find (category, command_path) for a tool_name by scanning categories."""
    for cat in _CATEGORY_DIRS:
        dynamic = taxonomy_tool_dir(_TOOLS_DIR, cat, tool_name) / "command.py"
        if dynamic.is_file():
            return cat, dynamic
        cmd = _TOOLS_DIR / cat / tool_name / "command.py"
        if cmd.is_file():
            return cat, cmd
        if cat == "game_systems":
            nested = list((_TOOLS_DIR / cat).glob(f"*/{tool_name}/command.py"))
            if nested:
                return cat, nested[0]
    return None


def _has_validation_case(tool_name: str, cases_text: str) -> bool:
    return bool(
        re.search(rf'"tool"\s*:\s*"{re.escape(tool_name)}"', cases_text)
        or re.search(rf"'tool'\s*:\s*'{re.escape(tool_name)}'", cases_text)
    )


def _in_dispatcher(tool_name: str, main_text: str) -> bool:
    m = re.search(r"def dispatch_tool\(.+?\n(.*?)^def ", main_text, re.DOTALL | re.MULTILINE)
    body = m.group(1) if m else main_text
    return f'"{tool_name}"' in body or f"'{tool_name}'" in body


def _in_registry(tool_name: str, registry_text: str) -> bool:
    return f'"{tool_name}"' in registry_text


def _in_category_init(category: str, tool_name: str, cmd_path: Optional[Path] = None) -> bool:
    if category == "game_systems" and cmd_path is not None and len(cmd_path.parents) >= 2:
        init_path = cmd_path.parents[1] / "__init__.py"
    else:
        init_path = _TOOLS_DIR / category / "__init__.py"
    content = _read_safe(init_path)
    return f"cmd_{tool_name}" in content or f"from .{tool_name}" in content


def _quality_checks(tool_name: str, cmd_content: str, registry_text: str, main_text: str, cases_text: str) -> Tuple[Dict[str, bool], int]:
    checks = {
        "has_summary": '"summary"' in cmd_content or "'summary'" in cmd_content,
        "has_timing": "elapsed_ms" in cmd_content,
        "has_validation": _has_validation_case(tool_name, cases_text),
        "in_registry": _in_registry(tool_name, registry_text),
        "in_dispatcher": _in_dispatcher(tool_name, main_text),
    }
    return checks, sum(1 for v in checks.values() if v)


def _version_from_level(level: int) -> str:
    level = max(0, int(level))
    major = level // 10
    minor = level % 10
    return f"V{major}.{minor}"


def _with_version_banner(
    content: str,
    version_before: str,
    version_after: str,
    improvement_pct: float,
    before_score: int,
    after_score: int,
    max_score: int,
    patches_applied: List[str],
) -> str:
    patch_text = ", ".join(patches_applied) if patches_applied else "no structural patches"
    banner_line = (
        f"# Tool Version: {version_after} (from {version_before}) | "
        f"Overall improvement since last version: {improvement_pct:+.1f}%"
    )
    detail_line = (
        f"# Upgrade Summary: baseline score {before_score}/{max_score} -> {after_score}/{max_score}; "
        f"changes: {patch_text}"
    )

    lines = content.splitlines()
    if lines and lines[0].startswith("# Tool Version:"):
        lines[0] = banner_line
        if len(lines) > 1 and lines[1].startswith("# Upgrade Summary:"):
            lines[1] = detail_line
        else:
            lines.insert(1, detail_line)
        updated = "\n".join(lines)
    else:
        updated = banner_line + "\n" + detail_line + "\n" + content

    if content.endswith("\n") and not updated.endswith("\n"):
        updated += "\n"
    return updated


# ── safe patches (no code changes to command.py) ─────────────────────────────

def _patch_registry(tool_name: str, category: str, registry_text: str) -> Tuple[str, bool]:
    """Insert a minimal TOOL_REGISTRY entry if missing."""
    if _in_registry(tool_name, registry_text):
        return registry_text, False
    # Find the last closing brace of TOOL_REGISTRY and insert before it
    entry = (
        f'    "{tool_name}": {{\n'
        f'        "category": "{category}",\n'
        f'        "description": "Tool generated by toolmaker (update this description).",\n'
        f'        "args": [{{"name": "target", "type": "str", "optional": True}}],\n'
        f'        "returns": "success, summary",\n'
        f'    }},\n'
    )
    # Insert just before the closing of TOOL_REGISTRY dict
    pattern = r'(TOOL_REGISTRY\s*=\s*\{.*?)(^\})'
    m = re.search(pattern, registry_text, re.DOTALL | re.MULTILINE)
    if m:
        new_text = registry_text[:m.end(1)] + entry + registry_text[m.end(1):]
        return new_text, True
    return registry_text, False


def _patch_category_init(category: str, tool_name: str, cmd_path: Optional[Path] = None) -> bool:
    """Add cmd_<tool_name> import to category __init__.py if missing."""
    if category == "game_systems" and cmd_path is not None and len(cmd_path.parents) >= 2:
        init_path = cmd_path.parents[1] / "__init__.py"
    else:
        init_path = _TOOLS_DIR / category / "__init__.py"
    content = _read_safe(init_path)
    if f"cmd_{tool_name}" in content or f"from .{tool_name}" in content:
        return False
    line = f"from .{tool_name} import cmd_{tool_name}\n"
    new_content = content.rstrip("\n") + "\n" + line
    return _write_safe(init_path, new_content)


def _patch_dispatcher(tool_name: str, main_text: str) -> Tuple[str, bool]:
    """Add a minimal dispatcher entry to main.py if missing."""
    if _in_dispatcher(tool_name, main_text):
        return main_text, False
    entry = _DISPATCHER_TEMPLATE.format(name=tool_name)
    # Insert just before the final "unknown tool" error line in dispatch_tool
    sentinel = '    print(f"unknown tool: {tool_name}"'
    idx = main_text.find(sentinel)
    if idx == -1:
        return main_text, False
    new_text = main_text[:idx] + entry + "\n" + main_text[idx:]
    return new_text, True


def _patch_validation_case(tool_name: str, cases_text: str) -> Tuple[str, bool]:
    """Add a minimal validation case if none exists for the tool."""
    if _has_validation_case(tool_name, cases_text):
        return cases_text, False
    case_entry = _VALIDATION_TEMPLATE.format(name=tool_name)
    # Insert just before the final ] that closes the cases list
    sentinel = "\n    ]  # end cases"
    if sentinel not in cases_text:
        # Try to find the last ] preceded by a }
        idx = cases_text.rfind("        },\n    ]")
        if idx == -1:
            return cases_text, False
        insert_at = idx + len("        },\n")
        new_text = cases_text[:insert_at] + case_entry + cases_text[insert_at:]
        return new_text, True
    idx = cases_text.find(sentinel)
    new_text = cases_text[:idx] + case_entry + cases_text[idx:]
    return new_text, True


# ── code patches (modify command.py) ─────────────────────────────────────────

def _patch_add_timing(content: str, tool_name: str) -> Tuple[str, bool]:
    """
    Add elapsed_ms tracking to the run_<name> function.
    Strategy: insert t0 = time.monotonic() after the function def line,
    and add payload["elapsed_ms"] = ... before each 'return 0,' or 'return code,'.
    Skips if elapsed_ms already present.
    """
    if "elapsed_ms" in content:
        return content, False

    # Ensure 'import time' is present
    if "import time" not in content:
        # Add after last existing import block
        lines = content.splitlines(keepends=True)
        last_import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                last_import_idx = i
        lines.insert(last_import_idx + 1, "import time\n")
        content = "".join(lines)

    # Add t0 after the run_ function signature
    run_fn_pattern = re.compile(
        rf"^(def run_{re.escape(tool_name)}\([^)]*\)[^:]*:)\s*\n",
        re.MULTILINE,
    )
    m = run_fn_pattern.search(content)
    if not m:
        return content, False

    insert_pos = m.end()
    # Find indent of first non-empty line inside function
    rest = content[insert_pos:]
    first_line_m = re.match(r"(\s+)\S", rest)
    indent = first_line_m.group(1) if first_line_m else "    "
    t0_line = f"{indent}t0 = time.monotonic()\n"
    content = content[:insert_pos] + t0_line + content[insert_pos:]

    # Add elapsed_ms before every 'return 0, payload' or 'return code, payload'
    # or 'return N, payload'
    content = re.sub(
        r"(\s+)(return \d+, payload\n|return code, payload\n)",
        lambda m2: (
            m2.group(1)
            + f'payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)\n'
            + m2.group(1)
            + m2.group(2)
        ),
        content,
    )
    return content, True


def _patch_add_summary(content: str, tool_name: str) -> Tuple[str, bool]:
    """
    Add payload.setdefault("summary", ...) before each return in run_<tool_name>.
    Uses setdefault so it never overwrites an existing "summary" key.
    Skips if "summary" already in content.
    """
    if '"summary"' in content or "'summary'" in content:
        return content, False

    default_msg = f"{tool_name} completed."
    content = re.sub(
        r"(\s+)(return \d+, payload\n|return code, payload\n)",
        lambda m2: (
            m2.group(1)
            + f'payload.setdefault("summary", "{default_msg}")\n'
            + m2.group(1)
            + m2.group(2)
        ),
        content,
    )
    return content, '"summary"' in content


# ── main entry ─────────────────────────────────────────────────────────────────

def run_tool_improver(repo_path: str, tool_name: Optional[str] = None) -> Tuple[int, Dict]:
    t0 = time.monotonic()

    if not tool_name:
        return 2, {"error": "missing_argument", "detail": "tool_name is required"}

    location = _find_tool(tool_name)
    if not location:
        return 2, {"error": "tool_not_found", "tool": tool_name,
                   "detail": f"No command.py found for tool '{tool_name}' in any category."}

    category, cmd_path = location
    patches_applied: List[str] = []
    files_modified: List[str] = []
    warnings: List[str] = []

    # Snapshot pre-upgrade baseline for human-readable progress reporting.
    cmd_before = _read_safe(cmd_path)
    registry_before = _read_safe(_REGISTRY)
    main_before = _read_safe(_MAIN_PY)
    cases_before = _read_safe(_CASES_PY)
    _checks_before, before_score = _quality_checks(
        tool_name,
        cmd_before,
        registry_before,
        main_before,
        cases_before,
    )
    max_score = 5

    # ── 1. Registry patch (no code change) ───────────────────────────────────
    registry_text = _read_safe(_REGISTRY)
    new_registry, changed = _patch_registry(tool_name, category, registry_text)
    if changed:
        if _write_safe(_REGISTRY, new_registry):
            patches_applied.append("added_to_registry")
            files_modified.append(str(_REGISTRY.relative_to(_AI_REPO_TOOLS)).replace("\\", "/"))
        else:
            warnings.append("Failed to write registry.py")

    # ── 2. Category __init__ patch ────────────────────────────────────────────
    if _patch_category_init(category, tool_name, cmd_path):
        patches_applied.append("added_to_category_init")
        if category == "game_systems" and len(cmd_path.parents) >= 2:
            files_modified.append(str((cmd_path.parents[1] / "__init__.py").relative_to(_AI_REPO_TOOLS)).replace("\\", "/"))
        else:
            files_modified.append(f"tools/{category}/__init__.py")

    # ── 3. Dispatcher patch ───────────────────────────────────────────────────
    main_text = _read_safe(_MAIN_PY)
    new_main, changed = _patch_dispatcher(tool_name, main_text)
    if changed:
        # Also need to add import at top
        if category == "game_systems" and len(cmd_path.parents) >= 2:
            subcategory = cmd_path.parents[1].name
            import_line = f"from tools.{category}.{subcategory}.{tool_name} import cmd_{tool_name}\n"
        else:
            import_line = f"from tools.{category}.{tool_name} import cmd_{tool_name}\n"
        if f"cmd_{tool_name}" not in new_main:
            # Find the last import block
            import_block_end = re.search(r"^# -- health", new_main, re.MULTILINE)
            if not import_block_end:
                import_block_end = re.search(r"^def cmd_help", new_main, re.MULTILINE)
            if import_block_end:
                new_main = new_main[:import_block_end.start()] + import_line + "\n" + new_main[import_block_end.start():]
        if _write_safe(_MAIN_PY, new_main):
            patches_applied.append("added_to_dispatcher")
            files_modified.append("main.py")
        else:
            warnings.append("Failed to write main.py")

    # ── 4. Validation case patch ──────────────────────────────────────────────
    cases_text = _read_safe(_CASES_PY)
    new_cases, changed = _patch_validation_case(tool_name, cases_text)
    if changed:
        if _write_safe(_CASES_PY, new_cases):
            patches_applied.append("added_validation_case")
            files_modified.append("validations/cases.py")
        else:
            warnings.append("Failed to write validations/cases.py")

    # ── 5. Code patches on command.py ─────────────────────────────────────────
    original_content = cmd_before
    content = original_content
    code_patches: List[str] = []

    content, timing_added = _patch_add_timing(content, tool_name)
    if timing_added:
        code_patches.append("added_elapsed_ms_timing")

    content, summary_added = _patch_add_summary(content, tool_name)
    if summary_added:
        code_patches.append("added_summary_field")

    if code_patches:
        compile_error = _compile_check(content)
        if compile_error:
            content = original_content
            warnings.append(f"Code patches reverted (compile failed): {compile_error}")
            code_patches = []
        else:
            if _write_safe(cmd_path, content):
                patches_applied.extend(code_patches)
                files_modified.append(
                    str(cmd_path.relative_to(_AI_REPO_TOOLS)).replace("\\", "/")
                )
            else:
                warnings.append("Failed to write command.py")
                code_patches = []

    # Compute post-upgrade baseline score after safe/code patches.
    cmd_after = _read_safe(cmd_path)
    registry_after = _read_safe(_REGISTRY)
    main_after = _read_safe(_MAIN_PY)
    cases_after = _read_safe(_CASES_PY)
    _checks_after, after_score = _quality_checks(
        tool_name,
        cmd_after,
        registry_after,
        main_after,
        cases_after,
    )
    improvement_pct = ((after_score - before_score) / max_score) * 100.0

    level_before, level_after, state_saved = _bump_upgrade_level(
        tool_name=tool_name,
        category=category,
        patches_applied=patches_applied,
        warnings=warnings,
    )
    if not state_saved:
        warnings.append("Failed to persist toolmaker_state.json")

    version_before = _version_from_level(level_before)
    version_after = _version_from_level(level_after)

    # Add/update a human-readable version banner at the top of the upgraded tool.
    banner_updated = _with_version_banner(
        content=cmd_after,
        version_before=version_before,
        version_after=version_after,
        improvement_pct=improvement_pct,
        before_score=before_score,
        after_score=after_score,
        max_score=max_score,
        patches_applied=patches_applied,
    )
    if banner_updated != cmd_after:
        if _write_safe(cmd_path, banner_updated):
            patches_applied.append("updated_version_banner")
            cmd_rel = str(cmd_path.relative_to(_AI_REPO_TOOLS)).replace("\\", "/")
            if cmd_rel not in files_modified:
                files_modified.append(cmd_rel)
        else:
            warnings.append("Failed to write version banner to command.py")

    elapsed_ms = round((time.monotonic() - t0) * 1000)
    payload = {
        "success": True,
        "tool_improver_mode": "in_place_improvement",
        "tool": tool_name,
        "category": category,
        "patches_applied": patches_applied,
        "files_modified": files_modified,
        "warnings": warnings,
        "no_changes_needed": len(patches_applied) == 0,
        "upgrade_level_before": level_before,
        "upgrade_level_after": level_after,
        "upgrade_level_incremented": True,
        "version_before": version_before,
        "version_after": version_after,
        "overall_improvement_pct_since_last": round(improvement_pct, 1),
        "overall_improvement_text": (
            f"Overall improvement since {version_before}: {improvement_pct:+.1f}% "
            f"(baseline score {before_score}/{max_score} -> {after_score}/{max_score})."
        ),
        "state_file": str(_STATE_JSON.relative_to(_AI_REPO_TOOLS)).replace("\\", "/"),
        "elapsed_ms": elapsed_ms,
        "summary": (
            f"Improved '{tool_name}': applied {len(patches_applied)} patch(es) "
            f"({', '.join(patches_applied) or 'none'}), "
            f"modified {len(files_modified)} file(s), "
            f"version {version_before} -> {version_after}, "
            f"overall improvement {improvement_pct:+.1f}%."
            + (f" Warnings: {warnings}" if warnings else "")
        ),
    }
    return 0, payload


def cmd_tool_improver(repo_path: str, tool_name: Optional[str] = None):
    code, payload = run_tool_improver(repo_path, tool_name)
    print(json.dumps(payload))
    return code, payload
