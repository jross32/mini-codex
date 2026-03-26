"""
reputation_system_generator - reputation system generator

Category: execution
Returns: success, summary, elapsed_ms
"""
import json
from typing import Dict, Tuple

from tools.execution.engine_core import run_engine_tool


def run_reputation_system_generator(repo_path: str) -> Tuple[int, Dict]:
    return run_engine_tool(repo_path, "reputation_system_generator")


def cmd_reputation_system_generator(repo_path: str):
    code, payload = run_reputation_system_generator(repo_path)
    print(json.dumps(payload))
    return code, payload
