"""
mission_system_generator - mission system generator

Category: execution
Returns: success, summary, elapsed_ms
"""
import json
from typing import Dict, Tuple

from tools.execution.engine_core import run_engine_tool


def run_mission_system_generator(repo_path: str) -> Tuple[int, Dict]:
    return run_engine_tool(repo_path, "mission_system_generator")


def cmd_mission_system_generator(repo_path: str):
    code, payload = run_mission_system_generator(repo_path)
    print(json.dumps(payload))
    return code, payload
