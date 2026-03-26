"""
roguelike_sim_builder - Build roguelike simulation project using generic engine pipeline

Category: execution
Returns: success, summary, elapsed_ms
"""
import json
from typing import Dict, Tuple

from tools.execution.engine_core import run_engine_tool


def run_roguelike_sim_builder(repo_path: str) -> Tuple[int, Dict]:
    return run_engine_tool(repo_path, "roguelike_sim_builder")


def cmd_roguelike_sim_builder(repo_path: str):
    code, payload = run_roguelike_sim_builder(repo_path)
    print(json.dumps(payload))
    return code, payload
