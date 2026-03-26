"""Compatibility alias: zoo_toolmaker_gen3 -> recursive_toolchain_gen3."""
import json
from typing import Dict, Tuple

from tools.project_generation.multi_project.execution.operations.tool_functions.recursive_toolchain.recursive_toolchain_gen3.command import (
    run_recursive_toolchain_gen3,
)


def run_zoo_toolmaker_gen3(repo_path: str) -> Tuple[int, Dict]:
    _, payload = run_recursive_toolchain_gen3(repo_path)
    payload["compatibility_alias"] = "zoo_toolmaker_gen3"
    payload["summary"] = "Compatibility alias executed recursive_toolchain_gen3 successfully."
    return 0, payload


def cmd_zoo_toolmaker_gen3(repo_path: str):
    code, payload = run_zoo_toolmaker_gen3(repo_path)
    print(json.dumps(payload))
    return code, payload
