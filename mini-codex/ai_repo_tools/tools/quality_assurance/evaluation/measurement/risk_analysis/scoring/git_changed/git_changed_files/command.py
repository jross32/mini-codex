import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _resolve_git_executable() -> Optional[str]:
    found = shutil.which("git")
    if found:
        return found

    # Common Windows install locations when git is not on PATH.
    candidates = [
        Path("C:/Program Files/Git/cmd/git.exe"),
        Path("C:/Program Files/Git/bin/git.exe"),
        Path("C:/Program Files (x86)/Git/cmd/git.exe"),
        Path("C:/Program Files (x86)/Git/bin/git.exe"),
        Path("C:/Program Files/GitHub Desktop/resources/app/git/cmd/git.exe"),
    ]

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        ghd_root = Path(local_app_data) / "GitHubDesktop"
        if ghd_root.exists():
            for p in sorted(ghd_root.glob("app-*/resources/app/git/cmd/git.exe"), reverse=True):
                candidates.append(p)

    for p in candidates:
        if p.exists():
            return str(p)
    return None


def _parse_porcelain_line(line: str) -> Optional[Dict]:
    """Parse one git status --porcelain=v1 line."""
    if len(line) < 3:
        return None

    x = line[0]
    y = line[1]
    raw_path = line[3:]

    # Rename/copy uses: old -> new
    old_path = None
    new_path = raw_path
    if " -> " in raw_path:
        old_path, new_path = raw_path.split(" -> ", 1)

    staged = x != " " and x != "?"
    unstaged = y != " " and y != "?"
    untracked = x == "?" and y == "?"
    conflicts = x == "U" or y == "U" or (x == "A" and y == "A") or (x == "D" and y == "D")

    return {
        "x": x,
        "y": y,
        "path": new_path,
        "old_path": old_path,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
        "conflict": conflicts,
        "status_code": f"{x}{y}",
    }


def run_git_changed_files(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()

    repo = Path(repo_path)
    if not repo.exists():
        return 2, {
            "success": False,
            "error": "missing_path",
            "detail": f"repo path does not exist: {repo_path}",
        }

    git_exe = _resolve_git_executable()
    if not git_exe:
        elapsed_ms = round((time.monotonic() - t0) * 1000)
        return 0, {
            "success": True,
            "tool": "git_changed_files",
            "repo": str(repo),
            "git_available": False,
            "is_git_repo": False,
            "changed_count": 0,
            "staged_count": 0,
            "unstaged_count": 0,
            "untracked_count": 0,
            "conflict_count": 0,
            "changed_files": [],
            "staged_files": [],
            "unstaged_files": [],
            "untracked_files": [],
            "conflict_files": [],
            "entries": [],
            "elapsed_ms": elapsed_ms,
            "summary": "Git executable not found; returning zero-change snapshot.",
        }

    # Detect non-git repos and return a successful no-change payload.
    try:
        rp = subprocess.run(
            [git_exe, "-C", str(repo), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except subprocess.TimeoutExpired:
        elapsed_ms = round((time.monotonic() - t0) * 1000)
        return 0, {
            "success": True,
            "tool": "git_changed_files",
            "repo": str(repo),
            "git_available": True,
            "is_git_repo": False,
            "changed_count": 0,
            "staged_count": 0,
            "unstaged_count": 0,
            "untracked_count": 0,
            "conflict_count": 0,
            "changed_files": [],
            "staged_files": [],
            "unstaged_files": [],
            "untracked_files": [],
            "conflict_files": [],
            "entries": [],
            "elapsed_ms": elapsed_ms,
            "summary": "Git repo check timed out; returning zero-change snapshot.",
        }

    is_git_repo = rp.returncode == 0 and (rp.stdout or "").strip().lower() == "true"
    if not is_git_repo:
        elapsed_ms = round((time.monotonic() - t0) * 1000)
        return 0, {
            "success": True,
            "tool": "git_changed_files",
            "repo": str(repo),
            "git_available": True,
            "is_git_repo": False,
            "changed_count": 0,
            "staged_count": 0,
            "unstaged_count": 0,
            "untracked_count": 0,
            "conflict_count": 0,
            "changed_files": [],
            "staged_files": [],
            "unstaged_files": [],
            "untracked_files": [],
            "conflict_files": [],
            "entries": [],
            "elapsed_ms": elapsed_ms,
            "summary": "Directory is not a git repository; returning zero-change snapshot.",
        }

    try:
        # Fast and stable for scripting.
        cp = subprocess.run(
            [git_exe, "-C", str(repo), "status", "--porcelain=v1"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError:
        return 2, {
            "success": False,
            "error": "git_not_found",
            "detail": "git executable was not found in PATH",
        }
    except subprocess.TimeoutExpired:
        return 2, {
            "success": False,
            "error": "timeout",
            "detail": "git status timed out after 10 seconds",
        }

    if cp.returncode != 0:
        stderr = (cp.stderr or "").strip()
        return 2, {
            "success": False,
            "error": "git_status_failed",
            "detail": stderr or "unknown git error",
            "exit_code": cp.returncode,
        }

    entries: List[Dict] = []
    for raw in (cp.stdout or "").splitlines():
        parsed = _parse_porcelain_line(raw)
        if parsed:
            entries.append(parsed)

    changed_files = sorted({e["path"] for e in entries})
    staged_files = sorted({e["path"] for e in entries if e["staged"]})
    unstaged_files = sorted({e["path"] for e in entries if e["unstaged"]})
    untracked_files = sorted({e["path"] for e in entries if e["untracked"]})
    conflict_files = sorted({e["path"] for e in entries if e["conflict"]})

    elapsed_ms = round((time.monotonic() - t0) * 1000)
    payload = {
        "success": True,
        "tool": "git_changed_files",
        "repo": str(repo),
        "git_available": True,
        "is_git_repo": True,
        "changed_count": len(changed_files),
        "staged_count": len(staged_files),
        "unstaged_count": len(unstaged_files),
        "untracked_count": len(untracked_files),
        "conflict_count": len(conflict_files),
        "changed_files": changed_files,
        "staged_files": staged_files,
        "unstaged_files": unstaged_files,
        "untracked_files": untracked_files,
        "conflict_files": conflict_files,
        "entries": entries,
        "elapsed_ms": elapsed_ms,
        "summary": (
            f"Found {len(changed_files)} changed file(s): "
            f"{len(staged_files)} staged, {len(unstaged_files)} unstaged, "
            f"{len(untracked_files)} untracked, {len(conflict_files)} conflicts."
        ),
    }
    return 0, payload


def cmd_git_changed_files(repo_path: str):
    code, payload = run_git_changed_files(repo_path)
    print(json.dumps(payload))
    return code, payload
