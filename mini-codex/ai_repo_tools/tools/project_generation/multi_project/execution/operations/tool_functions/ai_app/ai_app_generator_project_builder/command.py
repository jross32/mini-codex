"""Orchestrator: execute all AI app generation branches."""
import json
import time
from typing import Dict, Tuple

from tools.project_generation.multi_project.execution.operations.tool_functions.ai_app.ai_app_backend_branch.command import (
    run_ai_app_backend_branch,
)
from tools.project_generation.multi_project.execution.operations.tool_functions.ai_app.ai_app_frontend_branch.command import (
    run_ai_app_frontend_branch,
)
from tools.project_generation.multi_project.execution.operations.tool_functions.ai_app.ai_app_intent_branch.command import (
    run_ai_app_intent_branch,
)
from tools.project_generation.multi_project.execution.operations.tool_functions.ai_app.ai_app_plan_branch.command import (
    run_ai_app_plan_branch,
)
from tools.project_generation.multi_project.execution.operations.tool_functions.ai_app.ai_app_spec_branch.command import (
    run_ai_app_spec_branch,
)
from tools.project_generation.multi_project.execution.operations.tool_functions.ai_app.ai_app_validation_branch.command import (
    run_ai_app_validation_branch,
)
from tools.project_generation.multi_project.execution.operations.tool_functions.ai_app._pipeline_common import (
    project_root,
    write_text,
)


def run_ai_app_generator_project_builder(repo_path: str) -> Tuple[int, Dict]:
    """Build a runnable AI app generator test project under aish_tests."""
    t0 = time.monotonic()

    branch_runs = []
    for name, fn in [
        ("intent", run_ai_app_intent_branch),
        ("plan", run_ai_app_plan_branch),
        ("spec", run_ai_app_spec_branch),
        ("backend", run_ai_app_backend_branch),
        ("frontend", run_ai_app_frontend_branch),
    ]:
        code, result = fn(repo_path)
        branch_runs.append({"branch": name, "code": code, "result": result})
        if code != 0:
            payload = {
                "success": False,
                "failed_branch": name,
                "branch_runs": branch_runs,
                "elapsed_ms": round((time.monotonic() - t0) * 1000),
                "summary": f"Project builder failed at {name} branch.",
            }
            return code, payload

    root = project_root(repo_path)
    readme = """# AI App Generator Test Project

This project was generated through the branch-based AI app pipeline.

## Structure

- backend: Flask API for generation and job listing
- frontend: Static UI wired to backend API
- .ai_app_pipeline: branch artifacts (intent, plan, spec, validation)

## Run backend

```bash
pip install -r backend/requirements.txt
python backend/app.py
```

## Open frontend

Open frontend/index.html in a browser while backend is running.
"""
    compose = """version: '3.9'
services:
  api:
    image: python:3.11-slim
    working_dir: /app
    volumes:
      - ./backend:/app
    command: sh -c \"pip install -r requirements.txt && python app.py\"
    ports:
      - \"8000:8000\"
"""
    write_text(root / "README.md", readme)
    write_text(root / "docker-compose.yml", compose)

    validation_code, validation_result = run_ai_app_validation_branch(repo_path)
    branch_runs.append({"branch": "validation", "code": validation_code, "result": validation_result})
    if validation_code != 0:
        payload = {
            "success": False,
            "failed_branch": "validation",
            "branch_runs": branch_runs,
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "summary": "Project builder failed at validation branch.",
        }
        return validation_code, payload

    validation_result = branch_runs[-1]["result"]
    payload: Dict = {
        "success": bool(validation_result.get("success", False)),
        "ai_app_generator_project_builder_mode": "pipeline_executed",
        "project_path": "aish_tests/ai_app_generator",
        "branch_runs": branch_runs,
        "metrics": validation_result.get("metrics", {}),
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
        "summary": "AI app generator project built via 6-branch pipeline.",
    }
    return 0 if payload["success"] else 1, payload


def cmd_ai_app_generator_project_builder(repo_path: str):
    code, payload = run_ai_app_generator_project_builder(repo_path)
    print(json.dumps(payload))
    return code, payload
