"""
engine_reusability_score - Score generated modules for cross-project reuse quality

Category: execution
Returns: success, summary, elapsed_ms
"""
import json
from typing import Dict, Tuple

from tools.execution.engine_core import run_engine_tool


def run_engine_reusability_score(repo_path: str) -> Tuple[int, Dict]:
    return run_engine_tool(repo_path, "engine_reusability_score")


def cmd_engine_reusability_score(repo_path: str):
    code, payload = run_engine_reusability_score(repo_path)
    print(json.dumps(payload))
    return code, payload
