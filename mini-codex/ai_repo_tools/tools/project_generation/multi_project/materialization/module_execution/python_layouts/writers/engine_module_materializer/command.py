"""
engine_module_materializer - engine module materializer

Category: execution
Returns: success, summary, elapsed_ms
"""
import json
from typing import Dict, Tuple

from tools.execution.engine_core import run_engine_tool


def run_engine_module_materializer(repo_path: str) -> Tuple[int, Dict]:
    return run_engine_tool(repo_path, "engine_module_materializer")


def cmd_engine_module_materializer(repo_path: str):
    code, payload = run_engine_module_materializer(repo_path)
    print(json.dumps(payload))
    return code, payload
