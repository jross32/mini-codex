"""
engine_contract_generator - Generate cross-project interface contracts for modules

Category: execution
Returns: success, summary, elapsed_ms
"""
import json
from typing import Dict, Tuple

from tools.execution.engine_core import run_engine_tool


def run_engine_contract_generator(repo_path: str) -> Tuple[int, Dict]:
    return run_engine_tool(repo_path, "engine_contract_generator")


def cmd_engine_contract_generator(repo_path: str):
    code, payload = run_engine_contract_generator(repo_path)
    print(json.dumps(payload))
    return code, payload
