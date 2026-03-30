"""
tool_usage_counter_refresh - tool usage counter refresh

Category: execution
Returns: success, summary, elapsed_ms
"""
import json
from typing import Dict, Tuple

from tools.execution.engine_core import run_engine_tool


def run_tool_usage_counter_refresh(repo_path: str) -> Tuple[int, Dict]:
    return run_engine_tool(repo_path, "tool_usage_counter_refresh")


def cmd_tool_usage_counter_refresh(repo_path: str):
    code, payload = run_tool_usage_counter_refresh(repo_path)
    print(json.dumps(payload))
    return code, payload
