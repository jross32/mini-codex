"""
game_type_schema_validator - game type schema validator

Category: execution
Returns: success, summary, elapsed_ms
"""
import json
from typing import Dict, Tuple

from tools.execution.engine_core import run_engine_tool


def run_game_type_schema_validator(repo_path: str) -> Tuple[int, Dict]:
    return run_engine_tool(repo_path, "game_type_schema_validator")


def cmd_game_type_schema_validator(repo_path: str):
    code, payload = run_game_type_schema_validator(repo_path)
    print(json.dumps(payload))
    return code, payload
