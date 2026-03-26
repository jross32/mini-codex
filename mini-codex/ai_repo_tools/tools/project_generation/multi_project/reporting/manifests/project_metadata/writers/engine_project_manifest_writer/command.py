"""
engine_project_manifest_writer - Write project manifest for generated multi-project builds

Category: execution
Returns: success, summary, elapsed_ms
"""
import json
from typing import Dict, Tuple

from tools.execution.engine_core import run_engine_tool


def run_engine_project_manifest_writer(repo_path: str) -> Tuple[int, Dict]:
    return run_engine_tool(repo_path, "engine_project_manifest_writer")


def cmd_engine_project_manifest_writer(repo_path: str):
    code, payload = run_engine_project_manifest_writer(repo_path)
    print(json.dumps(payload))
    return code, payload
