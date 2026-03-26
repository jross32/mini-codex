"""Compatibility alias: zoo_toolmaker_gen4 -> recursive_toolchain_gen4."""
import json
from typing import Dict, Tuple

from tools.project_generation.multi_project.execution.operations.tool_functions.recursive_toolchain.recursive_toolchain_gen4.command import (
    run_recursive_toolchain_gen4,
)


def run_zoo_toolmaker_gen4(repo_path: str) -> Tuple[int, Dict]:
    _, payload = run_recursive_toolchain_gen4(repo_path)
    payload["compatibility_alias"] = "zoo_toolmaker_gen4"
    payload["summary"] = "Compatibility alias executed recursive_toolchain_gen4 successfully."
    return 0, payload


def cmd_zoo_toolmaker_gen4(repo_path: str):
    code, payload = run_zoo_toolmaker_gen4(repo_path)
    print(json.dumps(payload))
    return code, payload
