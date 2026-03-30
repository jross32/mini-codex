"""
economy_system_generator - economy system generator

Category: execution
Returns: success, summary, elapsed_ms
"""
import json
from typing import Dict, Tuple

from tools.execution.engine_core import run_engine_tool


def run_economy_system_generator(repo_path: str) -> Tuple[int, Dict]:
    return run_engine_tool(repo_path, "economy_system_generator")


def cmd_economy_system_generator(repo_path: str):
    code, payload = run_economy_system_generator(repo_path)
    print(json.dumps(payload))
    return code, payload
