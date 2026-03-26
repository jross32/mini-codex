#!/usr/bin/env python3
"""
repeated-friction summarizer — mini-codex

Walks a workspace root for tool_observations.jsonl files, merges friction
events across all runs and repos, ranks by frequency × static severity weight,
and emits a compact actionable ranked summary.

Usage:
  python ai_repo_tools/friction_summarizer.py
  python ai_repo_tools/friction_summarizer.py --root /path/to/workspace
  python ai_repo_tools/friction_summarizer.py --json        # JSON only
  python ai_repo_tools/friction_summarizer.py --top 10      # top 10 entries
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path


# ── directories to skip when walking the workspace ────────────────────────────
_SKIP_DIRS = {
    ".venv", "venv", "env", ".env",
    "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", ".git", ".hg",
    "dist", "build",
}


# ── static severity model ─────────────────────────────────────────────────────
# Score = count × severity_weight.  Weights are explicit and hand-set; no ML.
# Severity levels: high=3, medium=2, low=1.
_SEVERITY: dict[str, int] = {
    # ── failure_category values (from observation._classify_failure) ──────────
    "missing_dependency":  3,   # high  — env gap, blocks cmd_run
    "test_failure":        3,   # high  — test suite broken
    "runtime_error":       2,   # med   — tool raised an exception
    "parse_error":         2,   # med   — malformed JSON/config
    "missing_path":        2,   # med   — caller or tool sent bad path
    "timeout":             2,   # med   — subprocess too slow
    "permission":          2,   # med   — OS access problem
    "missing_argument":    1,   # low   — calling convention error
    "unknown":             1,   # low   — unclassified failure

    # ── gap_signal values (from observation._weak_and_gaps) ──────────────────
    "test_failures":       3,   # high  — cmd_run gap: tests red
    "parse_fallback":      2,   # med   — ai_read / artifact_read fell back
    "no_recommendations":  2,   # med   — test_select gave empty list
    "execution_timeout":   2,   # med   — cmd_run timed out
    "no_files_listed":     1,   # low   — repo_map found nothing
    "empty_content":       1,   # low   — file had 0 lines
}

# Candidate human-readable next actions per pattern value.
_CANDIDATE_ACTIONS: dict[str, str] = {
    # failure categories
    "missing_dependency":  "verify env deps / add install-check step before cmd_run",
    "test_failure":        "inspect failing tests / check fixture or dep readiness",
    "runtime_error":       "add structured error handling to tool output",
    "parse_error":         "improve JSON/config parser resilience in ai_read",
    "missing_path":        "improve file path validation at tool boundary",
    "timeout":             "add subprocess timeout handling / narrow test scope",
    "permission":          "add permission-error handler",
    "missing_argument":    "improve argument validation / check caller convention",
    "unknown":             "add better failure classification in observation.py",
    # gap signals
    "test_failures":       "investigate test failures / add dependency readiness check",
    "parse_fallback":      "improve file parser / add encoding handler for non-UTF-8",
    "no_recommendations":  "improve test_select import ranking heuristics",
    "execution_timeout":   "add execution timeout handling / narrow test scope",
    "no_files_listed":     "check repo_map filtering rules / verify repo path",
    "empty_content":       "add empty-file guard in tool",
}


# ── file discovery ────────────────────────────────────────────────────────────

def _should_skip(name: str) -> bool:
    """Return True if this directory name should not be descended into."""
    return name in _SKIP_DIRS or name.endswith(".egg-info")


def _find_observation_files(root: Path) -> list:
    """
    Walk the workspace tree and collect all tool_observations.jsonl files,
    skipping dependency/cache directories.
    """
    found = []
    for dirpath, dirnames, filenames in os.walk(str(root)):
        # Prune skip dirs in-place so os.walk doesn't descend into them.
        dirnames[:] = sorted(d for d in dirnames if not _should_skip(d))
        if "tool_observations.jsonl" in filenames:
            found.append(Path(dirpath) / "tool_observations.jsonl")
    return sorted(found)


# ── event parsing ─────────────────────────────────────────────────────────────

def _repo_label(obs_path: Path, root: Path) -> str:
    """Return a short workspace-relative label for the repo owning this file."""
    try:
        rel = obs_path.relative_to(root)
        parts = rel.parts
        # e.g. mini-codex/agent_logs/tool_observations.jsonl -> "mini-codex"
        return parts[0] if len(parts) >= 1 else str(rel.parent)
    except ValueError:
        return obs_path.parent.parent.name


def _read_events(obs_path: Path) -> list:
    """Read all valid JSONL event dicts from one observation file."""
    events = []
    try:
        with open(obs_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return events


# ── aggregation ───────────────────────────────────────────────────────────────

def _aggregate(obs_files: list, root: Path) -> dict:
    """
    Aggregate friction events across all observation files.

    Extracts three pattern types:
      failure_category  — from failed events (.success == False)
      gap_signal        — from .gap_signals lists (any event)
      weak_result       — from .weak_result == True (any event)

    Returns a dict with raw counts and accumulated pattern data.
    """
    total_events = 0
    repos_scanned: set = set()

    # key: (tool, pattern_type, pattern_value)
    # value: {"count": int, "repos": set}
    patterns: dict = defaultdict(lambda: {"count": 0, "repos": set()})

    for obs_path in obs_files:
        repo_label = _repo_label(obs_path, root)
        repos_scanned.add(repo_label)
        events = _read_events(obs_path)
        total_events += len(events)

        for event in events:
            tool = event.get("tool", "unknown")

            # ── failure_category ──────────────────────────────────────────────
            if not event.get("success", True):
                fc = event.get("failure_category") or "unknown"
                key = (tool, "failure_category", fc)
                patterns[key]["count"] += 1
                patterns[key]["repos"].add(repo_label)

            # ── gap_signals ───────────────────────────────────────────────────
            for sig in event.get("gap_signals", []):
                key = (tool, "gap_signal", sig)
                patterns[key]["count"] += 1
                patterns[key]["repos"].add(repo_label)

            # ── weak_result ───────────────────────────────────────────────────
            if event.get("weak_result"):
                key = (tool, "weak_result", "weak_result")
                patterns[key]["count"] += 1
                patterns[key]["repos"].add(repo_label)

    return {
        "total_files": len(obs_files),
        "total_events": total_events,
        "repos_scanned": sorted(repos_scanned),
        "patterns": patterns,
    }


# ── ranking ───────────────────────────────────────────────────────────────────

def _rank(agg: dict) -> list:
    """Compute score = count × severity_weight and return sorted entries."""
    ranked = []
    for (tool, pattern_type, pattern_value), data in agg["patterns"].items():
        severity = _SEVERITY.get(pattern_value, 1)
        score = data["count"] * severity
        repos = sorted(data["repos"])
        ranked.append({
            "tool":             tool,
            "pattern_type":     pattern_type,
            "pattern":          pattern_value,
            "count":            data["count"],
            "severity_weight":  severity,
            "score":            score,
            "repos":            repos,
            "sample_repo":      repos[0] if repos else "",
            "candidate_action": _CANDIDATE_ACTIONS.get(
                pattern_value, "investigate and add handler"
            ),
        })

    # Primary: score descending; tiebreaker: count desc, then tool + pattern alpha.
    ranked.sort(key=lambda x: (-x["score"], -x["count"], x["tool"], x["pattern"]))
    return ranked


# ── output formatters ─────────────────────────────────────────────────────────

def _print_report(result: dict) -> None:
    """Print a human-readable ranked friction table."""
    meta   = result["meta"]
    ranked = result["ranked"]

    W = 80
    print()
    print("=" * W)
    print("  mini-codex repeated-friction summarizer")
    print("=" * W)
    print(f"  workspace     : {meta['workspace_root']}")
    print(f"  repos scanned : {meta['repos_scanned_count']}"
          + (f"  ({', '.join(meta['repos_scanned'])})" if meta['repos_scanned'] else ""))
    print(f"  obs files     : {meta['total_files']}")
    print(f"  events scanned: {meta['total_events']}")
    print(f"  patterns found: {meta['total_patterns']}")
    if meta["top_n"]:
        print(f"  showing top   : {meta['top_n']}")
    print()

    if not ranked:
        print("  No friction patterns found in available observation data.")
        print()
        print("  This is expected when all observed tool runs succeeded without")
        print("  gap signals.  Run more agent sessions against real repos and")
        print("  re-run the summarizer to see ranked friction data.")
        print("=" * W)
        print()
        return

    # Column layout
    fmt = "{:<14} {:<16} {:<22} {:>5} {:>4} {:>6}  {}"
    print(fmt.format("tool", "pattern_type", "pattern", "count", "sev", "score", "candidate_action"))
    print("-" * W)

    for entry in ranked:
        action = entry["candidate_action"]
        if len(action) > 40:
            action = action[:37] + "..."
        print(fmt.format(
            entry["tool"][:14],
            entry["pattern_type"][:16],
            entry["pattern"][:22],
            entry["count"],
            entry["severity_weight"],
            entry["score"],
            action,
        ))

    print("=" * W)
    print()


# ── main public API ───────────────────────────────────────────────────────────

def summarize(root: Path, top: int = 20) -> dict:
    """
    Full summarization pass.

    Returns a structured dict with:
      meta   — stats about the scan
      ranked — list of ranked friction entries (up to top)
    """
    obs_files = _find_observation_files(root)
    agg       = _aggregate(obs_files, root)
    ranked    = _rank(agg)[:top] if top else _rank(agg)

    return {
        "meta": {
            "workspace_root":    str(root),
            "total_files":       agg["total_files"],
            "total_events":      agg["total_events"],
            "repos_scanned":     agg["repos_scanned"],
            "repos_scanned_count": len(agg["repos_scanned"]),
            "total_patterns":    len(agg["patterns"]),
            "top_n":             top,
        },
        "ranked": ranked,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="mini-codex repeated-friction summarizer"
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Workspace root to scan (default: parent of mini-codex directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_only",
        help="Emit JSON only (no human-readable table)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Maximum ranked entries to emit (default: 20, 0 = unlimited)",
    )
    args = parser.parse_args()

    if args.root:
        root = Path(args.root).resolve()
    else:
        # Default: resolve workspace root from script location.
        # Script lives at: <workspace>/mini-codex/ai_repo_tools/friction_summarizer.py
        # Parent chain:    ai_repo_tools -> mini-codex -> workspace
        _script = Path(__file__).resolve()
        root = _script.parent.parent.parent   # workspace root

    if not root.exists():
        print(f"ERROR: workspace root does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    result = summarize(root, top=args.top)

    if args.json_only:
        # Strip non-serialisable sets (already converted in _rank / _aggregate)
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_report(result)
        print(json.dumps(result, indent=2, default=str))
