"""
tool_dashboard_index - Generate an HTML index page linking all tool_library_dashboard*.html files under ai_repo_tools/tool_usage

Category: toolmaker
Returns: success, index_path, dashboard_count, summary, elapsed_ms
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple


def run_tool_dashboard_index(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()

    repo = Path(repo_path).resolve()
    usage_dir = repo / "ai_repo_tools" / "tool_usage"
    if not usage_dir.is_dir():
        return 1, {"success": False, "error": "tool_usage directory not found", "elapsed_ms": 0, "summary": "Missing tool_usage dir"}

    dashboards: List[Path] = sorted(usage_dir.glob("tool_library_dashboard*.html"))

    def _make_label(path: Path) -> str:
        name = path.stem  # e.g. tool_library_dashboard_toolmaker_top6
        parts = name.replace("tool_library_dashboard", "").strip("_").split("_")
        if not parts or parts == [""]:
            return "All Tools"
        return " ".join(p.capitalize() for p in parts if p)

    rows = []
    for dash in dashboards:
        label = _make_label(dash)
        rows.append(f'        <li><a href="{dash.name}">{label}</a></li>')

    rows_html = "\n".join(rows) if rows else "        <li><em>No dashboards generated yet. Run tool_library_report first.</em></li>"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Tool Library Dashboard Index</title>
  <style>
    body{{font-family:system-ui,sans-serif;max-width:700px;margin:60px auto;padding:0 20px;background:#0f0f12;color:#e0e0e0}}
    h1{{font-size:1.6rem;margin-bottom:.3rem;color:#7dd3fc}}
    .sub{{color:#94a3b8;font-size:.85rem;margin-bottom:2rem}}
    ul{{list-style:none;padding:0}}
    li{{margin:.6rem 0}}
    a{{display:inline-block;padding:.55rem 1.1rem;border-radius:6px;background:#1e293b;color:#7dd3fc;text-decoration:none;border:1px solid #334155;transition:background .2s}}
    a:hover{{background:#0ea5e9;color:#fff}}
    .count{{color:#64748b;font-size:.8rem;margin-top:2.5rem}}
  </style>
</head>
<body>
  <h1>&#128202; Tool Library Dashboard Index</h1>
  <div class="sub">Generated {now}</div>
  <ul>
{rows_html}
  </ul>
  <div class="count">{len(dashboards)} dashboard(s) available</div>
</body>
</html>"""

    index_path = usage_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")

    elapsed = round((time.monotonic() - t0) * 1000)
    return 0, {
        "success": True,
        "index_path": str(index_path.relative_to(repo)).replace("\\", "/"),
        "dashboard_count": len(dashboards),
        "dashboards": [d.name for d in dashboards],
        "elapsed_ms": elapsed,
        "summary": f"Generated dashboard index with {len(dashboards)} link(s) at ai_repo_tools/tool_usage/index.html.",
    }


def cmd_tool_dashboard_index(repo_path: str):
    code, payload = run_tool_dashboard_index(repo_path)
    print(json.dumps(payload))
    return code, payload

