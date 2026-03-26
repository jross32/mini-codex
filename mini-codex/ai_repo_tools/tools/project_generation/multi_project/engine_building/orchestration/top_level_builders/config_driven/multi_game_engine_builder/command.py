"""
multi_game_engine_builder - multi game engine builder

Category: execution
Returns: success, summary, elapsed_ms
"""
import json
from typing import Dict, Tuple

from tools.execution.engine_core import run_engine_tool


def run_multi_game_engine_builder(repo_path: str) -> Tuple[int, Dict]:
    return run_engine_tool(repo_path, "multi_game_engine_builder")


def cmd_multi_game_engine_builder(repo_path: str):
    code, payload = run_multi_game_engine_builder(repo_path)
    print(json.dumps(payload))
    return code, payload
