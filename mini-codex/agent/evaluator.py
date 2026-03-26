from typing import Dict, Any
import os
from agent.core_state import load_agent_core_state


_CFG_CACHE: Dict[str, Dict[str, Any]] = {}
_CFG_MTIME: Dict[str, float] = {}


def _get_cached_core_state(repo_path: str) -> Dict[str, Any]:
    """Load agent core state with cheap mtime-based cache invalidation."""
    state_path = os.path.join(repo_path, "agent_logs", "agent_core_state.json")
    try:
        mtime = os.path.getmtime(state_path)
    except OSError:
        # Fall back to default state and cache under sentinel mtime.
        mtime = -1.0

    cached = _CFG_CACHE.get(repo_path)
    if cached is not None and _CFG_MTIME.get(repo_path) == mtime:
        return cached

    cfg = load_agent_core_state(repo_path)
    _CFG_CACHE[repo_path] = cfg
    _CFG_MTIME[repo_path] = mtime
    return cfg


def evaluate_step(tool_result: Dict[str, Any], repo_path: str = ".") -> Dict[str, Any]:
    cfg = _get_cached_core_state(repo_path)
    success = bool(tool_result.get("success", False))
    warnings = tool_result.get("warnings", []) or []

    usefulness = int(cfg.get("failure_usefulness", 1) or 1)
    uncertainty_reduction = int(cfg.get("failure_uncertainty_reduction", 1) or 1)
    next_step_quality = int(cfg.get("failure_next_step_quality", 1) or 1)

    if success:
        usefulness = int(cfg.get("success_usefulness", 4) or 4)
        uncertainty_reduction = int(cfg.get("success_uncertainty_reduction", 3) or 3)
        next_step_quality = int(cfg.get("success_next_step_quality", 3) or 3)

    if warnings:
        penalty = int(cfg.get("warning_penalty", 1) or 1)
        usefulness = max(1, usefulness - penalty)
        next_step_quality = max(1, next_step_quality - penalty)

    if not success:
        fail_penalty = int(cfg.get("failure_penalty", 1) or 1)
        next_step_quality = max(1, next_step_quality - fail_penalty)

    return {
        "success": success,
        "usefulness": usefulness,
        "uncertainty_reduction": uncertainty_reduction,
        "next_step_quality": next_step_quality,
    }
