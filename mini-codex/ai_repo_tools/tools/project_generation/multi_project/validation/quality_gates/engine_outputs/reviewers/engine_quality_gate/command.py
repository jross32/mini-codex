"""
engine_quality_gate - engine quality gate

Category: execution
Returns: success, summary, elapsed_ms
"""
import json
from typing import Dict, Tuple

from tools.execution.engine_core import run_engine_tool


def run_engine_quality_gate(repo_path: str) -> Tuple[int, Dict]:
    return run_engine_tool(repo_path, "engine_quality_gate")


def cmd_engine_quality_gate(repo_path: str):
    code, payload = run_engine_quality_gate(repo_path)
    print(json.dumps(payload))
    return code, payload
