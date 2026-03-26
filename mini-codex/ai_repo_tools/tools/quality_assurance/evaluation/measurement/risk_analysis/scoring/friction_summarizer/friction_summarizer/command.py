import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from friction_summarizer import summarize


def run_friction_summarizer(repo_path: str, top: Optional[int] = 20) -> Tuple[int, Dict]:
    t0 = time.monotonic()

    try:
        top_n = 20 if top is None else int(top)
    except (TypeError, ValueError):
        return 2, {
            "success": False,
            "error": "invalid_argument",
            "detail": "top must be an integer",
        }

    if top_n < 0:
        return 2, {
            "success": False,
            "error": "invalid_argument",
            "detail": "top must be >= 0",
        }

    workspace_root = Path(repo_path).resolve().parent
    result = summarize(workspace_root, top=top_n)

    elapsed_ms = round((time.monotonic() - t0) * 1000)
    payload = {
        "success": True,
        "tool": "friction_summarizer",
        "workspace_root": str(workspace_root),
        "meta": result.get("meta", {}),
        "ranked": result.get("ranked", []),
        "elapsed_ms": elapsed_ms,
        "summary": (
            f"Friction summary scanned {result.get('meta', {}).get('total_events', 0)} events "
            f"across {result.get('meta', {}).get('repos_scanned_count', 0)} repos."
        ),
    }
    return 0, payload


def cmd_friction_summarizer(repo_path: str, top: Optional[int] = 20):
    code, payload = run_friction_summarizer(repo_path, top)
    print(json.dumps(payload))
    return code, payload
