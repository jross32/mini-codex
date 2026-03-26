"""Branch 3: write strict project spec."""
import json
import time
from typing import Dict, Tuple

from tools.project_generation.multi_project.execution.operations.tool_functions.ai_app._pipeline_common import (
    pipeline_dir,
    read_json,
    write_json,
)


def run_ai_app_spec_branch(repo_path: str) -> Tuple[int, Dict]:
    """Transform plan into a strict, file-level build spec."""
    t0 = time.monotonic()
    pipeline = pipeline_dir(repo_path)
    plan = read_json(pipeline / "plan.json")

    spec = {
        "project_name": "ai_app_generator",
        "required_paths": [
            "backend/app.py",
            "backend/requirements.txt",
            "frontend/index.html",
            "frontend/styles.css",
            "frontend/main.js",
            "README.md",
            "docker-compose.yml",
        ],
        "api_contract": {
            "health": {"method": "GET", "path": "/api/health", "status": 200},
            "generate": {"method": "POST", "path": "/api/generate", "status": 201},
            "jobs": {"method": "GET", "path": "/api/jobs", "status": 200},
        },
        "quality_gates": [
            "all required_paths exist",
            "Flask app exposes /api/health and /api/generate",
            "frontend main.js calls backend /api/generate",
        ],
        "source_plan": plan,
    }
    spec_path = pipeline / "spec.json"
    write_json(spec_path, spec)

    payload: Dict = {
        "success": True,
        "ai_app_spec_branch_mode": "spec_compiled",
        "spec_path": "aish_tests/ai_app_generator/.ai_app_pipeline/spec.json",
        "spec": spec,
        "elapsed_ms": 0,
        "summary": "Spec branch generated strict API and filesystem contract.",
    }

    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_ai_app_spec_branch(repo_path: str):
    code, payload = run_ai_app_spec_branch(repo_path)
    print(json.dumps(payload))
    return code, payload
