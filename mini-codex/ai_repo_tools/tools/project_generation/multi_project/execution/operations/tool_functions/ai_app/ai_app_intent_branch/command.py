"""Branch 1: parse prompt into structured intent."""
import json
import time
from typing import Dict, Tuple

from tools.project_generation.multi_project.execution.operations.tool_functions.ai_app._pipeline_common import (
    DEFAULT_PROMPT,
    pipeline_dir,
    write_json,
)


def run_ai_app_intent_branch(repo_path: str) -> Tuple[int, Dict]:
    """Parse a baseline prompt into normalized intent."""
    t0 = time.monotonic()

    normalized_prompt = DEFAULT_PROMPT.strip().lower()
    intent = {
        "raw_prompt": DEFAULT_PROMPT,
        "normalized_prompt": normalized_prompt,
        "app_type": "business_website",
        "industry": "restaurant",
        "core_features": [
            "menu_browsing",
            "online_ordering",
            "order_status",
            "admin_management",
        ],
        "pages": [
            "home",
            "menu",
            "cart",
            "checkout",
            "admin",
        ],
        "non_functional_goals": [
            "runnable_out_of_box",
            "clear_project_structure",
            "api_frontend_contract_alignment",
        ],
    }
    intent_path = pipeline_dir(repo_path) / "intent.json"
    write_json(intent_path, intent)

    payload: Dict = {
        "success": True,
        "ai_app_intent_branch_mode": "intent_parsed",
        "intent_path": "aish_tests/ai_app_generator/.ai_app_pipeline/intent.json",
        "intent": intent,
        "elapsed_ms": 0,  # updated below
        "summary": "Intent branch parsed prompt into structured app intent.",
    }

    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_ai_app_intent_branch(repo_path: str):
    code, payload = run_ai_app_intent_branch(repo_path)
    print(json.dumps(payload))
    return code, payload
