"""
engine_dependency_map_builder - Build dependency map for generated modules across systems

Category: execution
Returns: success, summary, elapsed_ms
"""
import json
from typing import Dict, Tuple

from tools.execution.engine_core import run_engine_tool


def run_engine_dependency_map_builder(repo_path: str) -> Tuple[int, Dict]:
    return run_engine_tool(repo_path, "engine_dependency_map_builder")


def cmd_engine_dependency_map_builder(repo_path: str):
    code, payload = run_engine_dependency_map_builder(repo_path)
    print(json.dumps(payload))
    return code, payload
