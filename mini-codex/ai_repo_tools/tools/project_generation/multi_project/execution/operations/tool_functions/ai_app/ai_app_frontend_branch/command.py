"""Branch 5: generate frontend skeleton and API client."""
import json
import time
from typing import Dict, Tuple

from tools.project_generation.multi_project.execution.operations.tool_functions.ai_app._pipeline_common import (
    project_root,
    ensure_project_dirs,
    write_text,
)


def run_ai_app_frontend_branch(repo_path: str) -> Tuple[int, Dict]:
    """Write static frontend that calls backend generate API."""
    t0 = time.monotonic()
    root = project_root(repo_path)
    ensure_project_dirs(repo_path)

    index_html = """<!doctype html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\">\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n  <title>AI App Generator</title>\n  <link rel=\"stylesheet\" href=\"styles.css\">\n</head>\n<body>\n  <main class=\"shell\">\n    <h1>AI App Generator</h1>\n    <p>Generate starter app artifacts from a prompt.</p>\n    <form id=\"gen-form\">\n      <textarea id=\"prompt\" placeholder=\"Describe the app you want\" required></textarea>\n      <button type=\"submit\">Generate</button>\n    </form>\n    <section>\n      <h2>Latest Result</h2>\n      <pre id=\"result\">No generation run yet.</pre>\n    </section>\n  </main>\n  <script src=\"main.js\"></script>\n</body>\n</html>\n"""
    styles_css = """body {\n  margin: 0;\n  font-family: \"Segoe UI\", Tahoma, sans-serif;\n  background: linear-gradient(135deg, #f8f4e6, #d7e7f5);\n  color: #1f2d3d;\n}\n\n.shell {\n  max-width: 820px;\n  margin: 2rem auto;\n  padding: 1.5rem;\n  background: rgba(255, 255, 255, 0.9);\n  border-radius: 14px;\n  box-shadow: 0 12px 28px rgba(25, 35, 45, 0.12);\n}\n\ntextarea {\n  width: 100%;\n  min-height: 140px;\n  margin: 0.75rem 0;\n  padding: 0.75rem;\n}\n\nbutton {\n  padding: 0.7rem 1.1rem;\n  border: 0;\n  border-radius: 8px;\n  background: #166088;\n  color: #fff;\n  cursor: pointer;\n}\n\npre {\n  background: #0c1a27;\n  color: #ccf2ff;\n  padding: 1rem;\n  border-radius: 8px;\n  overflow-x: auto;\n}\n"""
    main_js = """const form = document.getElementById(\"gen-form\");\nconst promptEl = document.getElementById(\"prompt\");\nconst resultEl = document.getElementById(\"result\");\n\nform.addEventListener(\"submit\", async (event) => {\n  event.preventDefault();\n  resultEl.textContent = \"Generating...\";\n\n  const response = await fetch(\"http://localhost:8000/api/generate\", {\n    method: \"POST\",\n    headers: { \"Content-Type\": \"application/json\" },\n    body: JSON.stringify({ prompt: promptEl.value }),\n  });\n\n  const payload = await response.json();\n  resultEl.textContent = JSON.stringify(payload, null, 2);\n});\n"""

    write_text(root / "frontend" / "index.html", index_html)
    write_text(root / "frontend" / "styles.css", styles_css)
    write_text(root / "frontend" / "main.js", main_js)

    payload: Dict = {
        "success": True,
        "ai_app_frontend_branch_mode": "frontend_generated",
        "frontend_files": [
            "aish_tests/ai_app_generator/frontend/index.html",
            "aish_tests/ai_app_generator/frontend/styles.css",
            "aish_tests/ai_app_generator/frontend/main.js",
        ],
        "elapsed_ms": 0,  # updated below
        "summary": "Frontend branch generated static UI and API client.",
    }

    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_ai_app_frontend_branch(repo_path: str):
    code, payload = run_ai_app_frontend_branch(repo_path)
    print(json.dumps(payload))
    return code, payload
