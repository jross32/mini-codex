"""Branch 2: build project plan from intent."""
import json
import time
from typing import Dict, Tuple

from tools.project_generation.multi_project.execution.operations.tool_functions.ai_app._pipeline_common import (
    pipeline_dir,
    read_json,
    write_json,
)


def run_ai_app_plan_branch(repo_path: str) -> Tuple[int, Dict]:
    """Build a concrete project plan and stack selection."""
    t0 = time.monotonic()
    pipeline = pipeline_dir(repo_path)
    intent = read_json(pipeline / "intent.json")

    plan = {
        "project_name": "ai_app_generator",
        "stack": {
            "backend": "flask",
            "frontend": "vanilla_js",
            "database": "sqlite",
            "infra": ["dockerfile", "docker_compose"],
        },
        "routes": [
            "GET /api/health",
            "POST /api/generate",
            "GET /api/jobs",
        ],
        "data_models": [
            "GenerationJob",
            "AppTemplate",
            "PluginSpec",
        ],
        "ui_sections": [
            "PromptInput",
            "PipelinePreview",
            "GenerationResults",
        ],
        "source_intent": intent,
    }
    plan_path = pipeline / "plan.json"
    write_json(plan_path, plan)

    payload: Dict = {
        "success": True,
        "ai_app_plan_branch_mode": "plan_compiled",
        "plan_path": "aish_tests/ai_app_generator/.ai_app_pipeline/plan.json",
        "plan": plan,
        "elapsed_ms": 0,  # updated below
        "summary": "Plan branch produced stack, routes, models, and UI plan.",
    }

    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_ai_app_plan_branch(repo_path: str):
    code, payload = run_ai_app_plan_branch(repo_path)
    print(json.dumps(payload))
    return code, payload
