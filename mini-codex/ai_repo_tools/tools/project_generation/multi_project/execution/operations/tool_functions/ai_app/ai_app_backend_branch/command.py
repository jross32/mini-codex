"""Branch 4: generate backend skeleton and API endpoints."""
import json
import time
from typing import Dict, Tuple

from tools.project_generation.multi_project.execution.operations.tool_functions.ai_app._pipeline_common import (
    ensure_project_dirs,
    project_root,
    write_text,
)


def run_ai_app_backend_branch(repo_path: str) -> Tuple[int, Dict]:
    """Write backend Flask service for generation pipeline."""
    t0 = time.monotonic()
    root = project_root(repo_path)
    ensure_project_dirs(repo_path)

    app_py = """from flask import Flask, jsonify, request

app = Flask(__name__)

JOBS = []


@app.get(\"/api/health\")
def health():
    return jsonify({\"status\": \"ok\", \"service\": \"ai_app_generator\"})


@app.post(\"/api/generate\")
def generate():
    body = request.get_json(silent=True) or {}
    prompt = (body.get(\"prompt\") or \"\").strip()
    if not prompt:
        return jsonify({\"error\": \"prompt is required\"}), 400
    job = {
        \"id\": len(JOBS) + 1,
        \"prompt\": prompt,
        \"status\": \"completed\",
        \"artifact\": f\"generated_app_{len(JOBS) + 1}\",
    }
    JOBS.append(job)
    return jsonify(job), 201


@app.get(\"/api/jobs\")
def jobs():
    return jsonify({\"jobs\": JOBS})


if __name__ == \"__main__\":
    app.run(host=\"0.0.0.0\", port=8000, debug=True)
"""
    requirements = "flask==3.0.3\n"

    write_text(root / "backend" / "app.py", app_py)
    write_text(root / "backend" / "requirements.txt", requirements)

    payload: Dict = {
        "success": True,
        "ai_app_backend_branch_mode": "backend_generated",
        "backend_files": [
            "aish_tests/ai_app_generator/backend/app.py",
            "aish_tests/ai_app_generator/backend/requirements.txt",
        ],
        "elapsed_ms": 0,
        "summary": "Backend branch generated Flask API and requirements.",
    }

    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_ai_app_backend_branch(repo_path: str):
    code, payload = run_ai_app_backend_branch(repo_path)
    print(json.dumps(payload))
    return code, payload
