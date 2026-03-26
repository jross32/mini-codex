# Tool Version: V0.5 (from V0.4) | Overall improvement since last version: +0.0%
# Upgrade Summary: baseline score 3/5 -> 3/5; changes: no structural patches
import os
from pathlib import Path


_MINI_CODEX_ROOT = Path(__file__).resolve().parents[4]


def _should_skip_ai_repo_tools(repo_path: str) -> bool:
    """Skip mini-codex's internal tool tree only during self-analysis."""
    return Path(repo_path).resolve() == _MINI_CODEX_ROOT


def cmd_repo_map(repo_path):
    files = []
    skip_ai_repo_tools = _should_skip_ai_repo_tools(repo_path)
    skipped_root = os.path.join(repo_path, "ai_repo_tools")
    for root, dirs, filenames in os.walk(repo_path):
        if skip_ai_repo_tools and root.startswith(skipped_root):
            continue
        for name in filenames:
            if name.startswith("."):
                continue
            path = os.path.relpath(os.path.join(root, name), repo_path)
            files.append(path.replace("\\", "/"))

    for path in sorted(files):
        print(path)

    return 0, {"file_count": len(files)}
