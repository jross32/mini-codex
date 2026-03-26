# Tool Version: V0.1 (from V0.0) | Overall improvement since last version: +20.0%
# Upgrade Summary: baseline score 4/5 -> 5/5; changes: added_elapsed_ms_timing
import json
import os
import re
import time
from collections import Counter
from typing import Dict, List, Optional, Tuple

from tools.shared import read_text_file_with_fallback


_EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
}

_ORIENTATION_NAMES = {
    "ai_start_here.md",
    "start_here.md",
    "readme.md",
}

_MAX_ORIENTATION_DOCS_TO_SCAN = 5


def _should_skip_dir(name: str) -> bool:
    return name in _EXCLUDE_DIRS


def _extract_doc_refs(text: str) -> List[str]:
    refs: List[str] = []
    seen = set()

    for match in re.findall(r"`([^`]+)`", text):
        candidate = match.strip().replace("\\", "/")
        if "/" in candidate or candidate.lower().endswith((".md", ".py", ".toml", ".json")):
            if candidate not in seen:
                seen.add(candidate)
                refs.append(candidate)

    for raw_line in text.splitlines():
        line = raw_line.strip().lstrip("-*").strip()
        line = re.sub(r"^\d+\.\s*", "", line)
        if not line:
            continue
        candidate = line.split()[0].strip().strip("`'\"").replace("\\", "/")
        if "/" in candidate and candidate.lower().endswith((".md", ".py", ".toml", ".json")):
            if candidate not in seen:
                seen.add(candidate)
                refs.append(candidate)

    return refs


def _iter_repo_files(repo_path: str, max_files: Optional[int]) -> Tuple[List[str], bool]:
    files: List[str] = []
    truncated = False

    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not _should_skip_dir(d)]

        for name in filenames:
            if name.startswith("."):
                continue
            rel = os.path.relpath(os.path.join(root, name), repo_path).replace("\\", "/")
            files.append(rel)
            if max_files is not None and len(files) >= max_files:
                truncated = True
                return files, truncated

    return files, truncated


def run_fast_analyze(repo_path: str, max_files: Optional[int] = None) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    """
    Fast deterministic repository analysis:
    - single filesystem pass
    - extension distribution
    - top directories
    - orientation docs and explicit references
    """
    t0 = time.monotonic()

    if max_files is not None and max_files <= 0:
        payload = {
            "success": False,
            "error": "invalid_argument",
            "detail": "max_files must be > 0",
        }
        payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)

        return 2, payload

    files, truncated = _iter_repo_files(repo_path, max_files)
    file_set = set(files)

    ext_counter: Counter = Counter()
    top_dirs: Counter = Counter()

    for rel in files:
        if "/" in rel:
            top_dirs[rel.split("/", 1)[0]] += 1
        else:
            top_dirs["."] += 1

        base = os.path.basename(rel)
        ext = os.path.splitext(base)[1].lower()
        if ext:
            ext_counter[ext] += 1
        else:
            ext_counter["<no_ext>"] += 1

    # Keep orientation doc ordering stable while preferring top-level docs first.
    orientation_docs_all = [f for f in files if os.path.basename(f).lower() in _ORIENTATION_NAMES]
    orientation_docs_all.sort(key=lambda f: ("/" in f, f.lower()))

    # Build basename index once to avoid repeated O(n) scans while resolving refs.
    basename_index: Dict[str, str] = {}
    for f in files:
        base = f.split("/")[-1]
        if base not in basename_index:
            basename_index[base] = f

    doc_refs: Dict[str, List[str]] = {}
    for doc in orientation_docs_all[:_MAX_ORIENTATION_DOCS_TO_SCAN]:
        abs_doc = os.path.join(repo_path, doc)
        try:
            text, _encoding = read_text_file_with_fallback(abs_doc)
        except Exception:
            continue
        refs = _extract_doc_refs(text)

        existing_refs = []
        for ref in refs:
            if ref in file_set:
                existing_refs.append(ref)
                continue
            base = ref.split("/")[-1]
            match = basename_index.get(base)
            if match:
                existing_refs.append(match)

        if existing_refs:
            doc_refs[doc] = existing_refs[:10]

    elapsed = round(time.monotonic() - t0, 3)

    payload = {
        "success": True,
        "repo_path": repo_path,
        "analysis_mode": "deterministic_single_pass",
        "duration_seconds": elapsed,
        "file_count": len(files),
        "truncated": truncated,
        "max_files": max_files,
        "top_extensions": [{"ext": k, "count": v} for k, v in ext_counter.most_common(12)],
        "top_directories": [{"dir": k, "count": v} for k, v in top_dirs.most_common(12)],
        "orientation_docs": orientation_docs_all[:10],
        "orientation_references": doc_refs,
        "summary": (
            f"Scanned {len(files)} files in {elapsed}s; "
            f"found {len(orientation_docs_all)} orientation docs and {sum(len(v) for v in doc_refs.values())} referenced paths."
        ),
    }

    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)


    return 0, payload


def run_fast_analyze_for_process(
    repo_path: str,
    max_files: Optional[int] = None,
    max_orientation_docs: int = 3,
) -> Tuple[int, Dict]:
    """
    Lightweight deterministic analysis for fast_process.
    Keeps only fields required for process planning.
    """
    t0 = time.monotonic()

    if max_files is not None and max_files <= 0:
        payload = {
            "success": False,
            "error": "invalid_argument",
            "detail": "max_files must be > 0",
        }
        payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)

        return 2, payload

    files, truncated = _iter_repo_files(repo_path, max_files)
    file_set = set(files)

    ext_counter: Counter = Counter()
    for rel in files:
        base = os.path.basename(rel)
        ext = os.path.splitext(base)[1].lower()
        if ext:
            ext_counter[ext] += 1
        else:
            ext_counter["<no_ext>"] += 1

    orientation_docs_all = [f for f in files if os.path.basename(f).lower() in _ORIENTATION_NAMES]
    orientation_docs_all.sort(key=lambda f: ("/" in f, f.lower()))

    basename_index: Dict[str, str] = {}
    for f in files:
        base = f.split("/")[-1]
        if base not in basename_index:
            basename_index[base] = f

    doc_refs: Dict[str, List[str]] = {}
    scan_limit = max(1, max_orientation_docs)
    for doc in orientation_docs_all[:scan_limit]:
        abs_doc = os.path.join(repo_path, doc)
        try:
            text, _encoding = read_text_file_with_fallback(abs_doc)
        except Exception:
            continue

        refs = _extract_doc_refs(text)
        existing_refs: List[str] = []
        for ref in refs:
            if ref in file_set:
                existing_refs.append(ref)
                continue
            base = ref.split("/")[-1]
            match = basename_index.get(base)
            if match:
                existing_refs.append(match)

        if existing_refs:
            doc_refs[doc] = existing_refs[:10]

    elapsed = round(time.monotonic() - t0, 3)
    payload = {
        "success": True,
        "repo_path": repo_path,
        "analysis_mode": "deterministic_single_pass_minimal",
        "duration_seconds": elapsed,
        "file_count": len(files),
        "truncated": truncated,
        "max_files": max_files,
        "top_extensions": [{"ext": k, "count": v} for k, v in ext_counter.most_common(12)],
        "orientation_docs": orientation_docs_all[:10],
        "orientation_references": doc_refs,
        "summary": (
            f"Minimal scan {len(files)} files in {elapsed}s; "
            f"orientation docs={len(orientation_docs_all)} refs={sum(len(v) for v in doc_refs.values())}."
        ),
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)

    return 0, payload


def cmd_fast_analyze(repo_path: str, max_files: Optional[int] = None):
    exit_code, payload = run_fast_analyze(repo_path, max_files)

    print(json.dumps(payload))
    return exit_code, payload
