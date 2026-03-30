"""
engine_mode_router - engine mode router

Category: execution
Returns: success, summary, elapsed_ms
"""
import json
from typing import Dict, Tuple

from tools.execution.engine_core import run_engine_tool


def run_engine_mode_router(repo_path: str) -> Tuple[int, Dict]:
    return run_engine_tool(repo_path, "engine_mode_router")


def cmd_engine_mode_router(repo_path: str):
    code, payload = run_engine_mode_router(repo_path)
    print(json.dumps(payload))
    return code, payload
