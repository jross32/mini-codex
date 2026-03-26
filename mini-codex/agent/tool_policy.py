from typing import Dict, List

# Tools proven safe enough to run by default in planning flows.
DEFAULT_SAFE_TOOLS = {"fast_process"}

# Helpful but not baseline replacements; use when explicitly needed.
OPTIONAL_FAST_TOOLS = {"fast_analyze", "fast_prepare", "fast_evaluate"}


def extract_planned_reads_from_fast_process(payload: Dict) -> List[str]:
    """Extract deterministic read targets from fast_process payload."""
    planned: List[str] = []
    seen = set()

    for action in payload.get("next_actions", []) or []:
        if not isinstance(action, str):
            continue
        if not action.startswith("read:"):
            continue
        path = action[5:].strip()
        if not path or path in seen:
            continue
        seen.add(path)
        planned.append(path)

    primary = payload.get("primary_orientation_doc")
    if isinstance(primary, str) and primary and primary not in seen:
        planned.insert(0, primary)

    return planned
