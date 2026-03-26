"""Compatibility alias: zoo_toolmaker_gen2 -> recursive_toolchain_gen2."""
import json
from typing import Dict, Tuple

from tools.project_generation.multi_project.execution.operations.tool_functions.recursive_toolchain.recursive_toolchain_gen2.command import (
    run_recursive_toolchain_gen2,
)


def run_zoo_toolmaker_gen2(repo_path: str) -> Tuple[int, Dict]:
    _, payload = run_recursive_toolchain_gen2(repo_path)
    payload["compatibility_alias"] = "zoo_toolmaker_gen2"
    payload["summary"] = "Compatibility alias executed recursive_toolchain_gen2 successfully."
    return 0, payload


def cmd_zoo_toolmaker_gen2(repo_path: str):
    code, payload = run_zoo_toolmaker_gen2(repo_path)
    print(json.dumps(payload))
    return code, payload
