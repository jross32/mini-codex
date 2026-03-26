"""
taxonomy_probe_execution - Probe tool for six-level taxonomy routing

Category: execution
Returns: success, summary, elapsed_ms

NOTE: This tool was scaffolded by toolmaker. Implement run_taxonomy_probe_execution() logic.
"""
import json
import time
from typing import Dict, Tuple

from tools.project_generation.multi_project.execution.operations.tool_functions.taxonomy_init.taxonomy_init_normalizer.command import (
    run_taxonomy_init_normalizer,
)
from tools.project_generation.multi_project.execution.operations.tool_functions.taxonomy_probe.taxonomy_probe_execution_status.command import (
    run_taxonomy_probe_execution_status,
)


def run_taxonomy_probe_execution(repo_path: str) -> Tuple[int, Dict]:
    """
    Probe tool for six-level taxonomy routing

    Returns: success, summary, elapsed_ms
    """
    t0 = time.monotonic()

    normalize_code, normalize_payload = run_taxonomy_init_normalizer(repo_path)
    status_code, status_payload = run_taxonomy_probe_execution_status(repo_path)

    success = normalize_code == 0 and status_code == 0 and bool(status_payload.get("success"))
    payload: Dict = {
        "success": success,
        "taxonomy_probe_execution_mode": "normalize_then_status",
        "normalizer": normalize_payload,
        "status": status_payload,
        "summary": (
            "Taxonomy probe executed successfully and package health is clean."
            if success
            else "Taxonomy probe executed but issues remain; inspect status payload."
        ),
    }

    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return (0 if success else 1), payload


def cmd_taxonomy_probe_execution(repo_path: str):
    code, payload = run_taxonomy_probe_execution(repo_path)
    print(json.dumps(payload))
    return code, payload
