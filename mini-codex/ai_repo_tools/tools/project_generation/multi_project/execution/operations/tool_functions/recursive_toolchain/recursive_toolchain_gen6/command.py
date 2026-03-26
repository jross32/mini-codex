"""Universal recursive toolchain generation - terminal generation 6."""
import json
import time
from pathlib import Path
from typing import Dict, Tuple


def run_recursive_toolchain_gen6(repo_path: str) -> Tuple[int, Dict]:
    """Write terminal generation-6 manifest for recursive toolchain expansion."""
    t0 = time.monotonic()
    generation = 6
    max_generation = 6
    root = Path(repo_path).resolve()
    output_dir = root / "ai_repo_tools" / "tool_usage" / "recursive_toolchain_generation"
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = output_dir / f"gen{generation}_manifest.json"
    manifest = {
        "generation": generation,
        "max_generation": max_generation,
        "source_tool": "recursive_toolchain_gen6",
        "next_generation_tool_prefix": None,
        "next_generation_tool_count": 0,
        "next_generation_tools": [],
        "terminal_generation": True,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    payload: Dict = {
        "success": True,
        "generation": generation,
        "max_generation": max_generation,
        "recursive_step_complete": True,
        "next_generation_ready": False,
        "next_generation": None,
        "next_tool_count": 0,
        "manifest_path": str(manifest_path.relative_to(root)).replace("\\", "/"),
        "summary": "Generation 6 reached terminal depth; recursion chain complete.",
    }

    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_recursive_toolchain_gen6(repo_path: str):
    code, payload = run_recursive_toolchain_gen6(repo_path)
    print(json.dumps(payload))
    return code, payload
