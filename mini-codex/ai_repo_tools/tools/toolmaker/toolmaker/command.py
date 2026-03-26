"""
toolmaker - Scaffold a new complete tool from a spec and wire it into the toolkit.

Given a tool spec, creates ALL associated files atomically:
  1. tools/<category>/<name>/command.py  — working tool implementation
  2. tools/<category>/<name>/__init__.py — package export
  3. tools/<category>/__init__.py        — updated to include new tool
  4. tools/registry.py                  — entry added to TOOL_REGISTRY
  5. ai_repo_tools/main.py              — import + dispatcher entry added
  6. validations/cases.py               — basic validation case added

Args:
  name        - snake_case tool name (e.g. "schema_diff")
  category    - existing category name (discovery|planning|evaluation|reading|execution|health|toolmaker)
  description - one-line description of what the tool does
  returns     - description of what the tool returns
  args_spec   - JSON array of arg dicts: [{"name": "x", "type": "str", "optional": true}, ...]

Returns a report of all files created and modified.
The generated command.py is a REAL working tool stub with proper structure,
consistent return schema (success, summary, elapsed_ms), and ready for
capability implementation.
"""
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tools.taxonomy import taxonomy_segments, taxonomy_tool_dir

_AI_REPO_TOOLS = Path(__file__).resolve().parents[3]
_TOOLS_DIR = _AI_REPO_TOOLS / "tools"
_MAIN_PY = _AI_REPO_TOOLS / "main.py"
_REGISTRY = _TOOLS_DIR / "registry.py"
_CASES_PY = _AI_REPO_TOOLS / "validations" / "cases.py"

_VALID_CATEGORIES = {
    "discovery", "planning", "evaluation", "reading",
    "execution", "health", "toolmaker", "game_systems",
}


def _game_systems_subcategory(name: str) -> str:
    if name.startswith("shop_"):
        return "shops"
    if name.startswith("monster_"):
        return "monsters"
    if name.startswith("character_"):
        return "character"
    if name.startswith("combat_"):
        return "combat"
    if name.startswith("rest_"):
        return "rest"
    if name.startswith("saveload_"):
        return "saveload"
    if name.startswith("ui_"):
        return "ui"
    if name.startswith("rpg_"):
        return "builders"
    if name.startswith("game_"):
        return "orchestration"
    if name in {"game_orchestrator", "v2_branch_probe_tool"}:
        return "orchestration"
    return "core"


def _resolve_tool_paths(category: str, name: str) -> Tuple[Path, str, str]:
    """Return (tool_dir, import_module_prefix, display_rel_dir)."""
    tool_dir = taxonomy_tool_dir(_TOOLS_DIR, category, name)
    segments = taxonomy_segments(category, name)
    rel_dir = "tools/" + "/".join(segments + [name])
    return tool_dir, ".".join(segments), rel_dir


def _category_init_path(category: str, name: str) -> Path:
    tool_dir, _, _ = _resolve_tool_paths(category, name)
    return tool_dir.parent / "__init__.py"


def _ensure_taxonomy_packages(category: str, name: str) -> None:
    tool_dir, _, _ = _resolve_tool_paths(category, name)
    current = _TOOLS_DIR
    for segment in taxonomy_segments(category, name):
        current = current / segment
        current.mkdir(parents=True, exist_ok=True)
        init_path = current / "__init__.py"
        if not init_path.exists():
            init_path.write_text("", encoding="utf-8")

# ── code generation ───────────────────────────────────────────────────────────

def _py_type(type_str: str, optional: bool) -> str:
    mapping = {"str": "str", "int": "int", "bool": "bool", "float": "float"}
    base = mapping.get(type_str, "str")
    return f"Optional[{base}]" if optional else base


def _default_for(arg: Dict) -> str:
    if arg.get("optional"):
        return " = None"
    return ""


def _generate_command_py(name: str, category: str, description: str,
                          args_spec: List[Dict], returns_desc: str) -> str:
    """Generate a fully working command.py for a new tool."""
    # Build function signature parts
    sig_parts = ["repo_path: str"]
    for arg in args_spec:
        aname = arg["name"]
        atype = _py_type(arg.get("type", "str"), arg.get("optional", False))
        default = _default_for(arg)
        sig_parts.append(f"{aname}: {atype}{default}")

    run_sig = f"def run_{name}({', '.join(sig_parts)}) -> Tuple[int, Dict]:"
    cmd_sig = f"def cmd_{name}({', '.join(sig_parts)}):"

    # Build cmd_ call args
    call_args = ["repo_path"] + [a["name"] for a in args_spec]
    call_args_str = ", ".join(call_args)

    # Build cmd_ pass-through args
    needs_optional = "Optional" in " ".join(_py_type(a.get("type", "str"), a.get("optional", False)) for a in args_spec)
    typing_imports = "Dict, Optional, Tuple" if needs_optional else "Dict, Tuple"

    # Build simple dispatcher arg extraction comment
    arg_extract_lines = []
    for i, arg in enumerate(args_spec):
        aname = arg["name"]
        if arg.get("optional"):
            arg_extract_lines.append(f"    {aname} = tool_args[{i}] if len(tool_args) > {i} else None")
        else:
            arg_extract_lines.append(f"    {aname} = tool_args[{i}] if len(tool_args) > {i} else None")

    # Payload fields from returns_desc keywords
    returns_fields = "\n".join([f'        "{name}_mode": "stub",'])

    code = f'''\
"""
{name} - {description}

Category: {category}
Returns: {returns_desc}

NOTE: This tool was scaffolded by toolmaker. Implement run_{name}() logic.
"""
import json
import time
from typing import {typing_imports}


def run_{name}({", ".join(sig_parts)}) -> Tuple[int, Dict]:
    """
    {description}

    Returns: {returns_desc}
    """
    t0 = time.monotonic()

    # TODO: Implement tool logic here.
    # Available inputs: {", ".join(a["name"] for a in args_spec) if args_spec else "none"}
    payload: Dict = {{
        "success": True,
{returns_fields}
        "elapsed_ms": 0,  # updated below
        "summary": f"{name} completed.",
    }}

    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_{name}({", ".join(sig_parts)}):
    code, payload = run_{name}({call_args_str})
    print(json.dumps(payload))
    return code, payload
'''
    return code


def _generate_init_py(name: str) -> str:
    return f"from .command import cmd_{name}\n"


def _category_init_export(category: str, name: str) -> str:
    return f"from .{name} import cmd_{name}\n"


def _registry_entry(name: str, category: str, description: str,
                    args_spec: List[Dict], returns_desc: str) -> str:
    args_repr = repr(args_spec)
    entry = (
        f'    "{name}": {{\n'
        f'        "category": "{category}",\n'
        f'        "description": "{description}",\n'
        f'        "args": {args_repr},\n'
        f'        "returns": "{returns_desc}",\n'
        f'    }},\n'
    )
    return entry


def _dispatcher_entry(name: str, args_spec: List[Dict]) -> str:
    """Generate a dispatcher block for main.py."""
    lines = [f'    if tool_name == "{name}":']
    for i, arg in enumerate(args_spec):
        aname = arg["name"]
        lines.append(f'        {aname} = tool_args[{i}] if len(tool_args) > {i} else None')
    call_args = ["repo_path"] + [a["name"] for a in args_spec]
    lines.append(f'        return cmd_{name}({", ".join(call_args)})')
    return "\n".join(lines) + "\n"


def _validation_case(name: str) -> str:
    return (
        f'        {{\n'
        f'            "name": "{name}_basic",\n'
        f'            "tool": "{name}",\n'
        f'            "repo": mc,\n'
        f'            "args": [],\n'
        f'            "expect": {{\n'
        f'                "success": True,\n'
        f'                "payload.summary": {{"not_none": True}},\n'
        f'            }},\n'
        f'        }},\n'
    )


# ── file modification helpers ─────────────────────────────────────────────────

def _read_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _write(path: Path, content: str) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return True
    except OSError:
        return False


def _add_to_category_init(category: str, name: str) -> bool:
    _ensure_taxonomy_packages(category, name)
    init_path = _category_init_path(category, name)
    content = _read_safe(init_path)
    export = _category_init_export(category, name)
    if f"cmd_{name}" in content:
        return False
    new_content = content.rstrip("\n") + "\n" + export
    return _write(init_path, new_content)


def _add_to_registry(name: str, category: str, description: str,
                     args_spec: List[Dict], returns_desc: str) -> bool:
    content = _read_safe(_REGISTRY)
    if f'"{name}"' in content:
        return False
    entry = _registry_entry(name, category, description, args_spec, returns_desc)
    # Insert before the closing brace of TOOL_REGISTRY
    pattern = r'(TOOL_REGISTRY\s*=\s*\{.*?)(^\})'
    m = re.search(pattern, content, re.DOTALL | re.MULTILINE)
    if not m:
        return False
    new_content = content[:m.end(1)] + entry + content[m.end(1):]
    return _write(_REGISTRY, new_content)


def _add_to_dispatcher_and_imports(name: str, category: str, args_spec: List[Dict]) -> bool:
    content = _read_safe(_MAIN_PY)
    if f'"{name}"' in content:
        return False

    _, import_category, _ = _resolve_tool_paths(category, name)

    # Add import line — find the health import block to insert after
    import_line = f"from tools.{import_category}.{name} import cmd_{name}\n"
    # Find last "from tools." import line
    last_import_m = None
    for m in re.finditer(r"^from tools\.\S+ import \S+\n", content, re.MULTILINE):
        last_import_m = m
    if last_import_m:
        content = content[:last_import_m.end()] + import_line + content[last_import_m.end():]
    else:
        # Fallback: prepend to file after SCRIPT_DIR block
        content = import_line + content

    # Add dispatcher entry before the unknown tool sentinel
    dispatcher_block = _dispatcher_entry(name, args_spec)
    sentinel = '    print(f"unknown tool: {tool_name}"'
    idx = content.find(sentinel)
    if idx == -1:
        return False
    content = content[:idx] + dispatcher_block + "\n" + content[idx:]
    return _write(_MAIN_PY, content)


def _add_validation_case(name: str) -> bool:
    content = _read_safe(_CASES_PY)
    if f'"tool": "{name}"' in content or f"'tool': '{name}'" in content:
        return False
    case = _validation_case(name)
    # Insert before last ] in the cases list
    idx = content.rfind("        },\n    ]")
    if idx == -1:
        return False
    insert_at = idx + len("        },\n")
    new_content = content[:insert_at] + case + content[insert_at:]
    return _write(_CASES_PY, new_content)


# ── main entry ─────────────────────────────────────────────────────────────────

def run_toolmaker(
    repo_path: str,
    name: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    args_spec_json: Optional[str] = None,
    returns_desc: Optional[str] = None,
) -> Tuple[int, Dict]:
    t0 = time.monotonic()

    if not name:
        return 2, {"error": "missing_argument", "detail": "name is required"}
    if not category:
        category = "health"  # safe default
    if category not in _VALID_CATEGORIES:
        return 2, {"error": "invalid_category", "detail": f"Must be one of: {sorted(_VALID_CATEGORIES)}"}
    if not description:
        description = f"{name} tool (add description)"
    if not returns_desc:
        returns_desc = "success, summary, elapsed_ms"

    # Parse args_spec
    args_spec: List[Dict] = []
    if args_spec_json:
        try:
            args_spec = json.loads(args_spec_json)
            if not isinstance(args_spec, list):
                args_spec = []
        except (json.JSONDecodeError, ValueError):
            args_spec = []

    # Validate name (must be valid Python identifier)
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        return 2, {"error": "invalid_name",
                   "detail": "name must be lowercase snake_case (e.g. 'my_tool')"}

    tool_dir, import_category, rel_dir = _resolve_tool_paths(category, name)
    if tool_dir.exists():
        return 2, {"error": "tool_exists",
                   "detail": f"Tool '{name}' already exists at {tool_dir}"}

    files_created: List[str] = []
    files_modified: List[str] = []
    errors: List[str] = []

    # 1. command.py
    cmd_content = _generate_command_py(name, category, description, args_spec, returns_desc)
    if _write(tool_dir / "command.py", cmd_content):
        files_created.append(f"{rel_dir}/command.py")
    else:
        errors.append(f"Failed to create {rel_dir}/command.py")

    # 2. __init__.py
    if _write(tool_dir / "__init__.py", _generate_init_py(name)):
        files_created.append(f"{rel_dir}/__init__.py")
    else:
        errors.append(f"Failed to create {rel_dir}/__init__.py")

    # 3. Category __init__.py
    if _add_to_category_init(category, name):
        files_modified.append(f"tools/{category}/__init__.py")

    # 4. registry.py
    if _add_to_registry(name, category, description, args_spec, returns_desc):
        files_modified.append("tools/registry.py")

    # 5. main.py
    if _add_to_dispatcher_and_imports(name, category, args_spec):
        files_modified.append("main.py")

    # 6. validations/cases.py
    if _add_validation_case(name):
        files_modified.append("validations/cases.py")

    elapsed_ms = round((time.monotonic() - t0) * 1000)
    success = len(errors) == 0

    payload = {
        "success": success,
        "toolmaker_mode": "scaffold_new_tool",
        "tool": name,
        "category": category,
        "files_created": files_created,
        "files_modified": files_modified,
        "errors": errors,
        "elapsed_ms": elapsed_ms,
        "next_step": (
            f"Implement run_{name}() in {rel_dir}/command.py, "
            f"then run: python ai_repo_tools/main.py {name}"
        ) if success else "Fix errors above before using tool.",
        "summary": (
            f"Created tool '{name}' in {category}/: "
            f"{len(files_created)} file(s) created, "
            f"{len(files_modified)} existing file(s) wired up."
            + (f" Errors: {errors}" if errors else "")
        ),
    }
    return 0 if success else 1, payload


def cmd_toolmaker(
    repo_path: str,
    name: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    args_spec_json: Optional[str] = None,
    returns_desc: Optional[str] = None,
):
    code, payload = run_toolmaker(
        repo_path, name=name, category=category,
        description=description, args_spec_json=args_spec_json,
        returns_desc=returns_desc,
    )
    print(json.dumps(payload))
    return code, payload
