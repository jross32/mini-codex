"""
tool_audit - Score and rank toolkit tools for continuous, open-ended upgrades.

Baseline quality dimensions (each worth 1 point, max baseline score = 5):
    1. has_summary     Does command.py return a "summary" key in its payload?
    2. has_timing      Does command.py track elapsed_ms?
    3. has_validation  Is there at least one validation case for this tool?
    4. in_registry     Is this tool in tools/registry.py?
    5. in_dispatcher   Is this tool handled in main.py dispatch_tool()?

Unlike a fixed maturity gate, this audit is continuous:
    - baseline score addresses foundational quality gaps
    - upgrade_level tracks how many upgrade passes each tool has received
    - opportunities provides rotating next improvements even after baseline is complete
"""
import ast
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from tools.registry import TOOL_CATEGORIES, TOOL_REGISTRY
from tools.taxonomy import taxonomy_tool_dir


def _find_ai_repo_tools_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "main.py").is_file() and (parent / "tools").is_dir():
            return parent
    raise RuntimeError("Could not locate ai_repo_tools root from tool_audit command path")


_AI_REPO_TOOLS = _find_ai_repo_tools_root()
_TOOLS_DIR = _AI_REPO_TOOLS / "tools"
_MAIN_PY = _AI_REPO_TOOLS / "main.py"
_REGISTRY = _TOOLS_DIR / "registry.py"
_CASES_PY = _AI_REPO_TOOLS / "validations" / "cases.py"
_STATE_JSON = _AI_REPO_TOOLS / "agent_logs" / "toolmaker_state.json"

_OPPORTUNITY_CYCLE = [
    "harden_error_handling",
    "improve_return_schema",
    "increase_test_depth",
    "optimize_runtime_paths",
    "improve_cli_ergonomics",
    "improve_observability",
    "improve_docs_and_examples",
    "strengthen_input_validation",
]


def _read_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _extract_validation_tools(cases_text: str) -> Set[str]:
    matches = re.findall(r'"tool"\s*:\s*"([^"]+)"', cases_text)
    matches.extend(re.findall(r"'tool'\s*:\s*'([^']+)'", cases_text))
    return set(matches)


def _extract_validation_counts(cases_text: str) -> Dict[str, int]:
    """Count how many validation cases exist per tool name."""
    counts: Dict[str, int] = {}
    matches = re.findall(r'"tool"\s*:\s*"([^"]+)"', cases_text)
    matches.extend(re.findall(r"'tool'\s*:\s*'([^']+)'", cases_text))
    for name in matches:
        counts[name] = counts.get(name, 0) + 1
    return counts


def _validation_depth_score(tool_name: str, counts: Dict[str, int], cases_text: str) -> int:
    """Return 0-3 validation depth score.
    0 = no cases
    1 = 1 case, no assertions beyond success
    2 = 1+ cases with contains/gte/not_none assertions
    3 = 2+ cases with assertions
    """
    n = counts.get(tool_name, 0)
    if n == 0:
        return 0
    # Check if any case for this tool has non-trivial assertions
    # Look for assertion keys beyond bare 'success': True
    tool_block_pattern = re.compile(
        r'"tool"\s*:\s*"' + re.escape(tool_name) + r'".*?(?="tool"|\]\s*$)',
        re.DOTALL,
    )
    blocks = tool_block_pattern.findall(cases_text)
    has_assertions = any(
        any(k in block for k in ('"contains"', '"gte"', '"not_none"', 'payload.', 'assert'))
        for block in blocks
    )
    if n >= 2 and has_assertions:
        return 3
    if has_assertions:
        return 2
    return 1


def _extract_dispatcher_tools(main_text: str) -> Set[str]:
    return set(re.findall(r'if tool_name == "([^"]+)":', main_text))


def _extract_key_usage(content: str) -> Set[str]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return set()

    keys: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    keys.add(key.value)
        elif isinstance(node, ast.Subscript):
            slice_node = node.slice
            if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, str):
                keys.add(slice_node.value)
    return keys


def _build_audit_context() -> Dict[str, Any]:
    registry_text = _read_safe(_REGISTRY)
    main_text = _read_safe(_MAIN_PY)
    cases_text = _read_safe(_CASES_PY)
    validation_counts = _extract_validation_counts(cases_text)
    return {
        "registry_text": registry_text,
        "validation_counts": validation_counts,
        "cases_text": cases_text,
        "main_text": main_text,
        "validation_tools": _extract_validation_tools(cases_text),
        "dispatcher_tools": _extract_dispatcher_tools(main_text),
        "has_dynamic_dispatch": "_dispatch_dynamic_registered_tool(repo_path, tool_name, tool_args)" in main_text,
    }


def _iter_tools() -> List[Tuple[str, str, Path]]:
    """Yield (tool_name, category, command_path) for every registered tool."""
    results: List[Tuple[str, str, Path]] = []
    category_order = {name: index for index, name in enumerate(TOOL_CATEGORIES.keys())}
    for tool_name, meta in TOOL_REGISTRY.items():
        category = str(meta.get("category", "unknown"))
        command_path = taxonomy_tool_dir(_TOOLS_DIR, category, tool_name) / "command.py"
        if not command_path.is_file():
            command_path = _TOOLS_DIR / category / tool_name / "command.py"
        results.append((tool_name, category, command_path))
    results.sort(key=lambda item: (category_order.get(item[1], 999), item[0]))
    return results


def _load_upgrade_levels() -> Dict[str, int]:
    """Read per-tool upgrade levels from toolmaker state (best-effort)."""
    if not _STATE_JSON.exists():
        return {}
    try:
        raw = json.loads(_STATE_JSON.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        levels = raw.get("levels", {})
        if not isinstance(levels, dict):
            return {}
        cleaned: Dict[str, int] = {}
        for k, v in levels.items():
            try:
                cleaned[str(k)] = int(v)
            except (TypeError, ValueError):
                continue
        return cleaned
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}


def _next_opportunities(tool_name: str, upgrade_level: int, missing: List[str]) -> List[str]:
    """Return a rotating shortlist of next improvements for a tool."""
    items: List[str] = []
    for missing_item in missing:
        items.append(f"fix_baseline_{missing_item}")

    if _OPPORTUNITY_CYCLE:
        start = max(0, upgrade_level) % len(_OPPORTUNITY_CYCLE)
        for index in range(3):
            items.append(_OPPORTUNITY_CYCLE[(start + index) % len(_OPPORTUNITY_CYCLE)])

    deduped: List[str] = []
    seen = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def _in_dispatcher(
    tool_name: str,
    dispatcher_tools: Set[str],
    has_dynamic_dispatch: bool,
    in_registry: bool,
    command_exists: bool,
) -> bool:
    if tool_name in dispatcher_tools:
        return True
    if has_dynamic_dispatch and in_registry and command_exists:
        return True
    return False


def _has_timing_key(content: str, key_usage: Set[str]) -> bool:
    return "elapsed_ms" in key_usage or "elapsed_ms" in content


def _has_summary_key(key_usage: Set[str]) -> bool:
    return "summary" in key_usage


def _score_tool(
    tool_name: str,
    category: str,
    cmd_path: Path,
    levels: Dict[str, int],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    content = _read_safe(cmd_path)
    key_usage = _extract_key_usage(content) if content else set()
    in_registry = tool_name in TOOL_REGISTRY
    command_exists = cmd_path.is_file()

    checks = {
        "has_summary": _has_summary_key(key_usage),
        "has_timing": _has_timing_key(content, key_usage),
        "has_validation": tool_name in context["validation_tools"],
        "in_registry": in_registry,
        "in_dispatcher": _in_dispatcher(
            tool_name,
            context["dispatcher_tools"],
            context["has_dynamic_dispatch"],
            in_registry,
            command_exists,
        ),
    }
    score = sum(checks.values())
    max_score = len(checks)
    missing = [name for name, ok in checks.items() if not ok]
    upgrade_level = max(0, int(levels.get(tool_name, 0)))
    opportunities = _next_opportunities(tool_name, upgrade_level, missing)

    validation_depth = _validation_depth_score(
        tool_name, context["validation_counts"], context["cases_text"]
    )
    if validation_depth == 0:
        pass  # has_validation already False
    elif validation_depth == 1 and "deepen_validation_assertions" not in opportunities:
        opportunities.append("deepen_validation_assertions")

    if not command_exists:
        opportunities = ["repair_missing_command"] + [item for item in opportunities if item != "repair_missing_command"]

    if missing:
        priority = "high" if score <= 2 else ("medium" if score <= 3 else "low")
    else:
        priority = "medium" if upgrade_level <= 1 else "low"

    return {
        "tool": tool_name,
        "category": category,
        "command_path": str(cmd_path.relative_to(_AI_REPO_TOOLS)).replace("\\", "/"),
        "command_exists": command_exists,
        "baseline_score": score,
        "baseline_max_score": max_score,
        "validation_depth": validation_depth,
        "checks": checks,
        "missing": missing,
        "upgrade_level": upgrade_level,
        "opportunities": opportunities,
        "needs_work": bool(missing),
        "eligible_for_upgrade": True,
        "priority": priority,
    }


def _cli_report(payload: Dict[str, Any], top_n: int) -> str:
    lines = [
        "Tool Audit",
        f"Tools: {payload['tools_found']} | Baseline gaps: {payload['baseline_gap_count']} | Complete: {payload['baseline_complete_count']}",
    ]
    if payload.get("category_filter"):
        lines.append(f"Category: {payload['category_filter']}")
    lines.extend(["", "Top Priorities"])

    for item in payload.get("candidates", [])[:top_n]:
        lines.append(
            f"  {item['tool']:<28} {item['baseline_score']}/{item['baseline_max_score']}  {item['priority']:<6} {item['category']}"
        )

    return "\n".join(lines)


def run_tool_audit(
    repo_path: str,
    output_format: str = "json",
    category_filter: Optional[str] = None,
    top_n: int = 20,
) -> Tuple[int, Dict[str, Any]]:
    t0 = time.monotonic()
    output_format = (output_format or "json").strip().lower()
    if output_format not in {"json", "table"}:
        return 2, {
            "success": False,
            "error": "invalid_output_format",
            "detail": "output_format must be one of: json, table",
            "summary": "Unsupported tool_audit output format.",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }

    normalized_category = (category_filter or "").strip().lower() or None
    if normalized_category and normalized_category not in TOOL_CATEGORIES:
        return 2, {
            "success": False,
            "error": "invalid_category_filter",
            "detail": f"Unknown category: {category_filter}",
            "summary": "Unsupported tool_audit category filter.",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }

    if top_n < 1:
        return 2, {
            "success": False,
            "error": "invalid_top_n",
            "detail": "top_n must be >= 1",
            "summary": "Unsupported tool_audit top_n value.",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }

    tools = _iter_tools()
    levels = _load_upgrade_levels()
    context = _build_audit_context()
    if not tools:
        payload = {
            "success": True,
            "tool_audit_mode": "continuous_quality_scan",
            "tools_found": 0,
            "candidates": [],
            "baseline_complete_tools": [],
            "improvement_order": [],
            "summary": "No tools found in the toolkit to audit.",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }
        return 0, payload

    scored = [_score_tool(name, cat, cmd, levels, context) for name, cat, cmd in tools]
    if normalized_category:
        scored = [item for item in scored if item["category"] == normalized_category]

    scored.sort(
        key=lambda item: (
            0 if item["missing"] else 1,
            item["baseline_score"],
            item["upgrade_level"],
            item["tool"],
        )
    )

    candidates = scored
    baseline_complete = [item for item in scored if not item["needs_work"]]
    baseline_gap_count = len([item for item in scored if item["needs_work"]])
    missing_command_count = len([item for item in scored if not item["command_exists"]])

    payload = {
        "success": True,
        "tool_audit_mode": "continuous_quality_scan",
        "tools_found": len(scored),
        "category_filter": normalized_category,
        "output_format": output_format,
        "top_n": top_n,
        "candidates": candidates,
        "baseline_complete_tools": [item["tool"] for item in baseline_complete],
        "baseline_gap_count": baseline_gap_count,
        "baseline_complete_count": len(baseline_complete),
        "missing_command_count": missing_command_count,
        "improvement_order": [item["tool"] for item in candidates],
        "top_priority": candidates[0]["tool"] if candidates else None,
        "all_baseline_scores": {item["tool"]: item["baseline_score"] for item in scored},
        "upgrade_levels": {item["tool"]: item["upgrade_level"] for item in scored},
        "reliability_notes": [
            "Audit signals use AST-aware key detection for summary and elapsed_ms where parsing succeeds.",
            "Registry, dispatcher, and validation sources are loaded once per run instead of per tool.",
            "Dynamic-dispatch credit requires both registry membership and a resolvable command path.",
        ],
        "summary": (
            f"Audited {len(scored)} tool(s): "
            f"{baseline_gap_count} have baseline gaps; "
            f"{len(baseline_complete)} are baseline-complete but still upgrade-eligible. "
            f"Top priority: {candidates[0]['tool']} "
            f"(baseline {candidates[0]['baseline_score']}/{candidates[0]['baseline_max_score']}, "
            f"level {candidates[0]['upgrade_level']}, "
            f"next: {candidates[0].get('opportunities', [])[:2]})."
            if candidates
            else "No candidate tools matched the requested filter."
        ),
    }
    payload["cli_view"] = _cli_report(payload, top_n=min(top_n, len(candidates)))
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_tool_audit(
    repo_path: str,
    output_format: str = "json",
    category_filter: Optional[str] = None,
    top_n: int = 20,
):
    code, payload = run_tool_audit(repo_path, output_format=output_format, category_filter=category_filter, top_n=top_n)
    if output_format == "table" and payload.get("success"):
        print(payload["cli_view"])
    else:
        print(json.dumps(payload))
    return code, payload
