"""
tool_library_report - Generate a unified report of toolkit tools with descriptions, usage counts, and weighted complexity scoring.

Category: toolmaker
Returns: success, summary, elapsed_ms
"""
import ast
import html
import json
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tools.registry import TOOL_CATEGORIES, TOOL_REGISTRY
from tools.taxonomy import taxonomy_tool_dir


_CONTROL_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.With,
    ast.AsyncWith,
    ast.Match,
    ast.IfExp,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)

_CONTROL_WEIGHTS = {
    ast.If: 1.5,
    ast.For: 2.0,
    ast.AsyncFor: 2.0,
    ast.While: 2.0,
    ast.Try: 2.5,
    ast.With: 0.5,
    ast.AsyncWith: 0.5,
    ast.Match: 2.0,
    ast.IfExp: 0.5,
    ast.ListComp: 0.75,
    ast.SetComp: 0.75,
    ast.DictComp: 0.75,
    ast.GeneratorExp: 0.75,
}

_FS_EFFECTS = {
    "write_text",
    "write_bytes",
    "mkdir",
    "rename",
    "replace",
    "unlink",
    "rmdir",
    "remove",
    "removedirs",
    "makedirs",
    "copy",
    "copy2",
    "move",
    "dump",
}
_PROCESS_EFFECTS = {"run", "Popen", "call", "check_output", "check_call", "system"}
_NETWORK_EFFECTS = {"get", "post", "put", "delete", "request", "urlopen", "create_connection"}


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}


def _slugify(value: str) -> str:
    safe = [char.lower() if char.isalnum() else "_" for char in value.strip()]
    collapsed = "".join(safe).strip("_")
    while "__" in collapsed:
        collapsed = collapsed.replace("__", "_")
    return collapsed or "all"


def _resolve_command_path(repo_root: Path, category: str, tool_name: str) -> Path:
    tools_root = repo_root / "ai_repo_tools" / "tools"
    taxonomy_path = taxonomy_tool_dir(tools_root, category, tool_name) / "command.py"
    if taxonomy_path.is_file():
        return taxonomy_path
    legacy_path = tools_root / category / tool_name / "command.py"
    return legacy_path


def _load_usage(repo_root: Path) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    usage: Dict[str, Dict[str, Any]] = {}
    notes: List[str] = []

    observation_summary = repo_root / "agent_logs" / "tool_observations_summary.json"
    if observation_summary.is_file():
        data = _read_json(observation_summary)
        tool_counts = data.get("tool_counts", {}) if isinstance(data, dict) else {}
        if isinstance(tool_counts, dict):
            for tool_name, count in tool_counts.items():
                usage[str(tool_name)] = {
                    "count": int(count),
                    "last_called_utc": None,
                    "source": "observation_summary",
                }
            notes.append("Merged usage counts from agent_logs/tool_observations_summary.json.")

    usage_counter = repo_root / "ai_repo_tools" / "tool_usage" / "usage_counter_ai.json"
    if usage_counter.is_file():
        data = _read_json(usage_counter)
        tools = data.get("tools", {}) if isinstance(data, dict) else {}
        if isinstance(tools, dict):
            for tool_name, meta in tools.items():
                if not isinstance(meta, dict):
                    continue
                prior = usage.get(str(tool_name), {"count": 0, "last_called_utc": None, "source": "usage_counter"})
                prior["count"] = max(int(prior.get("count", 0)), int(meta.get("count", 0)))
                prior["last_called_utc"] = meta.get("last_called_utc") or prior.get("last_called_utc")
                prior["source"] = "merged"
                usage[str(tool_name)] = prior
            notes.append("Merged usage metadata from ai_repo_tools/tool_usage/usage_counter_ai.json.")

    if not usage:
        notes.append("No usage sources were found; usage counts default to 0.")
    return usage, notes


def _count_loc(text: str) -> int:
    count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            count += 1
    return count


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def _max_nesting(node: ast.AST, depth: int = 0) -> int:
    here = depth + 1 if isinstance(node, _CONTROL_NODES) else depth
    child_depths = [_max_nesting(child, here) for child in ast.iter_child_nodes(node)]
    return max([here] + child_depths) if child_depths else here


def _analyze_complexity(command_path: Path, arg_spec: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not command_path.is_file():
        return {
            "score": None,
            "tier": "missing",
            "components": {},
            "details": {"missing_command": True},
        }

    text = command_path.read_text(encoding="utf-8")
    loc = _count_loc(text)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(text)
    except SyntaxError:
        return {
            "score": None,
            "tier": "broken",
            "components": {},
            "details": {"syntax_error": True, "loc": loc},
        }

    import_count = 0
    tool_imports = 0
    function_count = 0
    class_count = 0
    branch_weight = 0.0
    fs_effects = 0
    process_effects = 0
    network_effects = 0
    tool_calls = 0
    run_engine_calls = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            import_count += len(node.names)
            for alias in node.names:
                if alias.name.startswith("tools."):
                    tool_imports += 1
        elif isinstance(node, ast.ImportFrom):
            import_count += len(node.names)
            if (node.module or "").startswith("tools"):
                tool_imports += len(node.names)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_count += 1
        elif isinstance(node, ast.ClassDef):
            class_count += 1

        for kind, weight in _CONTROL_WEIGHTS.items():
            if isinstance(node, kind):
                branch_weight += weight
                break

        if isinstance(node, ast.Call):
            name = _call_name(node.func)
            leaf = name.split(".")[-1]
            if leaf in _FS_EFFECTS or name in {"Path.write_text", "Path.mkdir"}:
                fs_effects += 1
            if leaf in _PROCESS_EFFECTS or name.startswith("subprocess."):
                process_effects += 1
            if leaf in _NETWORK_EFFECTS or name.startswith("requests."):
                network_effects += 1
            if name.startswith("run_") or name.startswith("cmd_"):
                tool_calls += 1
            if leaf == "run_engine_tool":
                run_engine_calls += 1

    nesting = _max_nesting(tree)
    arg_count = len(arg_spec)
    optional_count = len([arg for arg in arg_spec if arg.get("optional")])

    components = {
        "size": min(15.0, loc / 12.0),
        "branching": min(20.0, branch_weight * 1.6),
        "nesting": min(10.0, max(0, nesting - 1) * 2.0),
        "interface": min(10.0, arg_count * 2.0 + optional_count * 1.0),
        "dependencies": min(15.0, import_count * 0.4 + tool_imports * 1.5),
        "side_effects": min(15.0, fs_effects * 1.8 + process_effects * 3.0 + network_effects * 3.0),
        "surface_area": min(5.0, function_count * 0.35 + class_count * 1.2),
        "orchestration": min(10.0, tool_calls * 1.4 + run_engine_calls * 2.5),
    }
    score = round(sum(components.values()), 2)

    if score >= 80:
        tier = "platform"
    elif score >= 60:
        tier = "orchestrator"
    elif score >= 40:
        tier = "high"
    elif score >= 20:
        tier = "moderate"
    else:
        tier = "atomic"

    details = {
        "loc": loc,
        "imports": import_count,
        "tool_imports": tool_imports,
        "functions": function_count,
        "classes": class_count,
        "branch_weight": round(branch_weight, 2),
        "max_nesting": nesting,
        "arg_count": arg_count,
        "optional_args": optional_count,
        "fs_effects": fs_effects,
        "process_effects": process_effects,
        "network_effects": network_effects,
        "tool_calls": tool_calls,
        "run_engine_calls": run_engine_calls,
    }
    return {"score": score, "tier": tier, "components": components, "details": details}


def _render_dashboard_html(report: Dict[str, Any], title_suffix: str = "") -> str:
    page_title = f"Tool Library Dashboard{title_suffix}"
    report_json = json.dumps(report)
    escaped_title = html.escape(page_title)
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{escaped_title}</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --panel: #fffaf3;
      --ink: #1d2a2f;
      --muted: #5d6a70;
      --accent: #0f766e;
      --accent-2: #c2410c;
      --line: #dccfbd;
      --shadow: 0 18px 40px rgba(29, 42, 47, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Georgia, 'Times New Roman', serif; background: linear-gradient(160deg, #efe6d8 0%, var(--bg) 45%, #f8f4ee 100%); color: var(--ink); }}
    .wrap {{ max-width: 1180px; margin: 0 auto; padding: 32px 20px 48px; }}
    .hero {{ display: grid; gap: 16px; margin-bottom: 28px; }}
    .kicker {{ color: var(--accent-2); text-transform: uppercase; letter-spacing: 0.12em; font-size: 12px; font-weight: 700; }}
    h1 {{ margin: 0; font-size: clamp(32px, 5vw, 56px); line-height: 0.95; }}
    .sub {{ color: var(--muted); max-width: 760px; font-size: 18px; }}
    .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 20px 0 8px; }}
    .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 18px; padding: 16px 18px; box-shadow: var(--shadow); }}
    .stat-label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .stat-value {{ font-size: 32px; font-weight: 700; margin-top: 6px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-top: 18px; }}
    table {{ width: 100%; border-collapse: collapse; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; }}
    th, td {{ text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }}
    th {{ color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .pill {{ display: inline-block; padding: 3px 8px; border-radius: 999px; background: rgba(15, 118, 110, 0.1); color: var(--accent); font-size: 12px; }}
    .muted {{ color: var(--muted); }}
    .notes {{ margin-top: 22px; }}
    ul {{ margin: 10px 0 0; padding-left: 18px; }}
    @media (max-width: 720px) {{ .wrap {{ padding: 20px 14px 32px; }} h1 {{ line-height: 1.02; }} }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"hero\">
      <div class=\"kicker\">Toolkit Observatory</div>
      <h1>{escaped_title}</h1>
      <div class=\"sub\">Inventory, usage, complexity, and health signals for the current tool library snapshot.</div>
      <div class=\"stats\" id=\"stats\"></div>
    </section>
    <section class=\"grid\">
      <div class=\"card\"><h2>Top Used</h2><table id=\"top-used\"></table></div>
      <div class=\"card\"><h2>Top Complexity</h2><table id=\"top-complexity\"></table></div>
    </section>
    <section class=\"grid\">
      <div class=\"card\"><h2>Category Summary</h2><table id=\"categories\"></table></div>
      <div class=\"card\"><h2>Broken Tools</h2><table id=\"broken-tools\"></table></div>
    </section>
    <section class=\"card notes\">
      <h2>Notes</h2>
      <ul id=\"notes\"></ul>
    </section>
  </div>
  <script>
    const REPORT = {report_json};

    function renderTable(id, headers, rows) {{
      const table = document.getElementById(id);
      const head = `<thead><tr>${{headers.map(h => `<th>${{h}}</th>`).join('')}}</tr></thead>`;
      const body = `<tbody>${{rows.map(row => `<tr>${{row.map(cell => `<td>${{cell}}</td>`).join('')}}</tr>`).join('')}}</tbody>`;
      table.innerHTML = head + body;
    }}

    const stats = [
      ['Visible Tools', REPORT.total_tools],
      ['Broken Tools', REPORT.broken_tool_count || 0],
      ['Category Filter', REPORT.category_filter || 'all'],
      ['Top N', REPORT.top_n || REPORT.top_used.length],
    ];
    document.getElementById('stats').innerHTML = stats.map(([label, value]) => `
      <div class=\"card\">
        <div class=\"stat-label\">${{label}}</div>
        <div class=\"stat-value\">${{value}}</div>
      </div>
    `).join('');

    renderTable('top-used', ['Tool', 'Usage', 'Category'], (REPORT.top_used || []).map(item => [item.tool, item.usage_count, `<span class=\"pill\">${{item.category}}</span>`]));
    renderTable('top-complexity', ['Tool', 'Score', 'Tier'], (REPORT.top_complexity || []).map(item => [item.tool, item.complexity_score ?? 'n/a', `<span class=\"pill\">${{item.complexity_tier}}</span>`]));

    const categories = Object.entries(REPORT.categories || REPORT.category_summary || {{}}).map(([name, item]) => [
      name,
      item.count ?? '',
      item.usage_total ?? '',
      item.avg_complexity ?? 'n/a'
    ]);
    renderTable('categories', ['Category', 'Count', 'Usage', 'Avg Complexity'], categories);

    renderTable('broken-tools', ['Tool', 'Category', 'Path'], (REPORT.broken_tools || REPORT.broken_tools_preview || []).slice(0, REPORT.top_n || 10).map(item => [item.tool, item.category, `<span class=\"muted\">${{item.command_path || ''}}</span>`]));

    document.getElementById('notes').innerHTML = (REPORT.notes || []).map(note => `<li>${{note}}</li>`).join('');
  </script>
</body>
</html>
"""


def _human_report(
    entries: List[Dict[str, Any]],
    category_summary: Dict[str, Any],
    notes: List[str],
    broken_tools: List[Dict[str, Any]],
    category_filter: Optional[str],
    top_n: int,
) -> Dict[str, Any]:
    top_used = sorted(entries, key=lambda item: (-item["usage_count"], item["tool"]))[:top_n]
    scored_entries = [item for item in entries if isinstance(item["complexity_score"], (int, float))]
    top_complex = sorted(scored_entries, key=lambda item: (-item["complexity_score"], item["tool"]))[:top_n]
    return {
        "title": "Tool Library Report",
        "subtitle": "Inventory, usage, and weighted complexity scoring for the toolkit",
        "total_tools": len(entries),
        "category_filter": category_filter,
        "top_n": top_n,
        "broken_tool_count": len(broken_tools),
        "top_used": [
            {"tool": item["tool"], "usage_count": item["usage_count"], "category": item["category"]}
            for item in top_used
        ],
        "top_complexity": [
            {
                "tool": item["tool"],
                "complexity_score": item["complexity_score"],
                "complexity_tier": item["complexity_tier"],
                "category": item["category"],
            }
            for item in top_complex
        ],
        "broken_tools_preview": [
            {
                "tool": item["tool"],
                "category": item["category"],
                "command_path": item["command_path"],
            }
            for item in broken_tools[:top_n]
        ],
        "category_summary": category_summary,
        "notes": notes,
    }


def _cli_report(payload: Dict[str, Any]) -> str:
    lines = [
        "Tool Library Report",
        f"Tools: {payload['total_tools']} | Broken: {payload['broken_tool_count']}",
    ]

    if payload.get("category_filter"):
        lines.append(f"Category: {payload['category_filter']}")
    lines.extend(["", "Top Used"])

    for item in payload.get("top_used", [])[: payload.get("top_n", 10)]:
        lines.append(f"  {item['tool']:<28} {item['usage_count']:>5}  {item.get('category', 'unknown')}")

    lines.extend(["", "Top Complexity"])
    for item in payload.get("top_complexity", [])[: payload.get("top_n", 10)]:
        score = item.get("complexity_score")
        score_text = f"{score:.2f}" if isinstance(score, (int, float)) else "n/a"
        lines.append(
            f"  {item['tool']:<28} {score_text:>6}  {item.get('complexity_tier', 'unknown'):<12} {item.get('category', 'unknown')}"
        )

    preview = payload.get("broken_tools_preview", [])
    if preview:
        lines.extend(["", "Broken Tool Preview"])
        for item in preview[: payload.get("top_n", 10)]:
            lines.append(f"  {item['tool']:<28} {item.get('category', 'unknown')}")

    return "\n".join(lines)


def run_tool_library_report(
    repo_path: str,
    output_format: str = "json",
    category_filter: Optional[str] = None,
    top_n: int = 10,
) -> Tuple[int, Dict[str, Any]]:
    """
    Generate a unified report of toolkit tools with descriptions, usage counts, and weighted complexity scoring.

    Returns: success, summary, elapsed_ms
    """
    t0 = time.monotonic()
    output_format = (output_format or "json").strip().lower()
    if output_format not in {"json", "table"}:
        payload: Dict[str, Any] = {
            "success": False,
            "error": "invalid_output_format",
            "detail": "output_format must be one of: json, table",
            "summary": "Unsupported tool_library_report output format.",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }
        return 2, payload

    normalized_category = (category_filter or "").strip().lower() or None
    if normalized_category and normalized_category not in TOOL_CATEGORIES:
        payload = {
            "success": False,
            "error": "invalid_category_filter",
            "detail": f"Unknown category: {category_filter}",
            "summary": "Unsupported tool_library_report category filter.",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }
        return 2, payload

    if top_n < 1:
        payload = {
            "success": False,
            "error": "invalid_top_n",
            "detail": "top_n must be >= 1",
            "summary": "Unsupported tool_library_report top_n value.",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }
        return 2, payload

    repo_root = Path(repo_path)
    ai_repo_tools_root = repo_root / "ai_repo_tools"
    if not ai_repo_tools_root.is_dir():
        payload = {
            "success": False,
            "error": "ai_repo_tools_not_found",
            "summary": "Could not locate ai_repo_tools root from repo path.",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }
        return 2, payload

    usage, notes = _load_usage(repo_root)
    entries: List[Dict[str, Any]] = []

    for tool_name, meta in sorted(TOOL_REGISTRY.items()):
        category = str(meta.get("category", "unknown"))
        command_path = _resolve_command_path(repo_root, category, tool_name)
        complexity = _analyze_complexity(command_path, meta.get("args", []))
        usage_meta = usage.get(tool_name, {})
        entries.append(
            {
                "tool": tool_name,
                "category": category,
                "description": meta.get("description", ""),
                "args": meta.get("args", []),
                "returns": meta.get("returns", ""),
                "command_path": str(command_path.relative_to(repo_root)).replace("\\", "/") if command_path.exists() else None,
                "usage_count": int(usage_meta.get("count", 0)),
                "last_called_utc": usage_meta.get("last_called_utc"),
                "usage_source": usage_meta.get("source", "none"),
                "complexity_score": complexity["score"],
                "complexity_tier": complexity["tier"],
                "complexity_components": complexity["components"],
                "complexity_details": complexity["details"],
            }
        )

    filtered_entries = [item for item in entries if item["category"] == normalized_category] if normalized_category else list(entries)
    category_summary: Dict[str, Any] = {}
    for entry in filtered_entries:
        summary = category_summary.setdefault(
            entry["category"],
            {"count": 0, "usage_total": 0, "complexity_total": 0.0, "max_complexity": 0.0},
        )
        summary["count"] += 1
        summary["usage_total"] += entry["usage_count"]
        if isinstance(entry["complexity_score"], (int, float)):
            summary["complexity_total"] += entry["complexity_score"]
            summary["max_complexity"] = max(summary["max_complexity"], entry["complexity_score"])
            summary["scored_count"] = summary.get("scored_count", 0) + 1

    for category_name, summary in category_summary.items():
        scored_count = max(1, summary.get("scored_count", 0))
        summary["avg_complexity"] = round(summary["complexity_total"] / scored_count, 2) if summary.get("scored_count", 0) else None
        summary["description"] = TOOL_CATEGORIES.get(category_name, {}).get("description", "")
        del summary["complexity_total"]
        if "scored_count" in summary:
            del summary["scored_count"]

    top_used = sorted(filtered_entries, key=lambda item: (-item["usage_count"], item["tool"]))[:top_n]
    scored_entries = [item for item in filtered_entries if isinstance(item["complexity_score"], (int, float))]
    broken_tools = [item for item in filtered_entries if item["complexity_tier"] == "broken"]
    top_complex = sorted(scored_entries, key=lambda item: (-item["complexity_score"], item["tool"]))[:top_n]

    title_suffix = f" - {normalized_category}" if normalized_category else ""
    report_ai = {
        "schema": "tool_library_report.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_tools": len(filtered_entries),
        "total_tools_all": len(entries),
        "category_filter": normalized_category,
        "top_n": top_n,
        "broken_tool_count": len(broken_tools),
        "categories": category_summary,
        "top_used": top_used,
        "top_complexity": top_complex,
        "broken_tools": [
            {
                "tool": item["tool"],
                "category": item["category"],
                "command_path": item["command_path"],
            }
            for item in broken_tools
        ],
        "tools": filtered_entries,
        "complexity_model": {
            "goal": "Score cognitive and operational complexity of each tool command implementation on a 0-100 scale.",
            "components": [
                "size",
                "branching",
                "nesting",
                "interface",
                "dependencies",
                "side_effects",
                "surface_area",
                "orchestration",
            ],
            "tiers": {
                "atomic": "0-19",
                "moderate": "20-39",
                "high": "40-59",
                "orchestrator": "60-79",
                "platform": "80+",
            },
        },
        "notes": notes,
    }
    report_human = _human_report(filtered_entries, category_summary, notes, broken_tools, normalized_category, top_n)
    dashboard_html = _render_dashboard_html(report_ai, title_suffix=title_suffix)

    usage_dir = ai_repo_tools_root / "tool_usage"
    usage_dir.mkdir(parents=True, exist_ok=True)
    suffix_parts: List[str] = []
    if normalized_category:
        suffix_parts.append(_slugify(normalized_category))
    if top_n != 10:
        suffix_parts.append(f"top{top_n}")
    suffix = f"_{'_'.join(suffix_parts)}" if suffix_parts else ""

    ai_path = usage_dir / f"tool_library_report{suffix}_ai.json"
    human_path = usage_dir / f"tool_library_report{suffix}_human.json"
    dashboard_path = usage_dir / f"tool_library_dashboard{suffix}.html"
    ai_path.write_text(json.dumps(report_ai, indent=2), encoding="utf-8")
    human_path.write_text(json.dumps(report_human, indent=2), encoding="utf-8")
    dashboard_path.write_text(dashboard_html, encoding="utf-8")

    payload: Dict[str, Any] = {
        "success": True,
        "tool_library_report_mode": "catalog_usage_complexity",
        "total_tools": len(filtered_entries),
        "total_tools_all": len(entries),
        "category_filter": normalized_category,
        "top_n": top_n,
        "report_path": str(ai_path.relative_to(repo_root)).replace("\\", "/"),
        "human_report_path": str(human_path.relative_to(repo_root)).replace("\\", "/"),
        "dashboard_path": str(dashboard_path.relative_to(repo_root)).replace("\\", "/"),
        "output_format": output_format,
        "broken_tool_count": len(broken_tools),
        "broken_tools_preview": [
            {"tool": item["tool"], "category": item["category"], "command_path": item["command_path"]}
            for item in broken_tools[:top_n]
        ],
        "top_used": [
            {"tool": item["tool"], "usage_count": item["usage_count"], "category": item["category"]}
            for item in top_used
        ],
        "top_complexity": [
            {
                "tool": item["tool"],
                "complexity_score": item["complexity_score"],
                "complexity_tier": item["complexity_tier"],
                "category": item["category"],
            }
            for item in top_complex
        ],
        "cli_view": _cli_report(
            {
                "total_tools": len(filtered_entries),
                "broken_tool_count": len(broken_tools),
                "category_filter": normalized_category,
                "top_n": top_n,
                "top_used": [
                    {"tool": item["tool"], "usage_count": item["usage_count"], "category": item["category"]}
                    for item in top_used
                ],
                "top_complexity": [
                    {
                        "tool": item["tool"],
                        "complexity_score": item["complexity_score"],
                        "complexity_tier": item["complexity_tier"],
                        "category": item["category"],
                    }
                    for item in top_complex
                ],
                "broken_tools_preview": [
                    {"tool": item["tool"], "category": item["category"], "command_path": item["command_path"]}
                    for item in broken_tools[:top_n]
                ],
            }
        ),
        "summary": "Generated unified tool library report with inventory, merged usage counts, and weighted complexity scoring.",
    }

    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_tool_library_report(
    repo_path: str,
    output_format: str = "json",
    category_filter: Optional[str] = None,
    top_n: int = 10,
):
    code, payload = run_tool_library_report(
        repo_path,
        output_format=output_format,
        category_filter=category_filter,
        top_n=top_n,
    )
    if output_format == "table" and payload.get("success"):
        print(payload["cli_view"])
    else:
        print(json.dumps(payload))
    return code, payload
