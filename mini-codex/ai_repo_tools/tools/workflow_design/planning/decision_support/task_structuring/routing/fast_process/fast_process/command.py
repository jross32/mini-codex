import json
from typing import Dict, List, Optional, Tuple

from tools.discovery.fast_analyze.command import run_fast_analyze_for_process


def _pick_primary_orientation_doc(orientation_docs: List[str]) -> Optional[str]:
    if not orientation_docs:
        return None

    # Prefer top-level orientation docs first.
    top_level = [d for d in orientation_docs if "/" not in d]
    if top_level:
        for preferred in ("AI_START_HERE.md", "START_HERE.md", "README.md"):
            if preferred in top_level:
                return preferred
        return sorted(top_level)[0]

    for preferred in ("AI_START_HERE.md", "START_HERE.md", "README.md"):
        if preferred in orientation_docs:
            return preferred

    return orientation_docs[0]


def _pick_followups(primary_doc: Optional[str], orientation_references: Dict[str, List[str]]) -> List[str]:
    if not primary_doc:
        return []
    refs = orientation_references.get(primary_doc, [])
    if not refs:
        return []

    # Prefer docs first, preserve first-seen order.
    docs = [r for r in refs if r.lower().endswith(".md")]
    others = [r for r in refs if not r.lower().endswith(".md")]
    return (docs + others)[:8]


def _pick_top_extension(top_extensions: List[Dict]) -> str:
    if not top_extensions:
        return "unknown"
    return top_extensions[0].get("ext", "unknown")


def _build_next_actions(primary_doc: Optional[str], followups: List[str]) -> List[str]:
    actions: List[str] = []
    if primary_doc:
        actions.append(f"read:{primary_doc}")
    for ref in followups[:2]:
        actions.append(f"read:{ref}")
    if not actions:
        actions.append("read:first_python_file")
    return actions


def run_fast_process(repo_path: str, max_files: Optional[int] = None) -> Tuple[int, Dict]:
    code, analysis = run_fast_analyze_for_process(repo_path, max_files=max_files, max_orientation_docs=3)
    if code != 0:
        payload = {
            "success": False,
            "error": "upstream_fast_analyze_failed",
            "analysis": analysis,
        }
        return code, payload

    orientation_docs = analysis.get("orientation_docs", [])
    orientation_refs = analysis.get("orientation_references", {})
    primary_doc = _pick_primary_orientation_doc(orientation_docs)
    followups = _pick_followups(primary_doc, orientation_refs)

    top_ext = _pick_top_extension(analysis.get("top_extensions", []))

    payload = {
        "success": True,
        "repo_path": repo_path,
        "process_mode": "deterministic_rule_plan",
        "file_count": analysis.get("file_count", 0),
        "duration_seconds": analysis.get("duration_seconds", 0.0),
        "primary_orientation_doc": primary_doc,
        "recommended_followups": followups,
        "next_actions": _build_next_actions(primary_doc, followups),
        "dominant_extension": top_ext,
        "analysis_summary": analysis.get("summary", ""),
        "summary": (
            f"Primary doc: {primary_doc or 'none'}; "
            f"follow-ups: {len(followups)}; "
            f"dominant extension: {top_ext}."
        ),
    }
    return 0, payload


def cmd_fast_process(repo_path: str, max_files: Optional[int] = None):
    code, payload = run_fast_process(repo_path, max_files=max_files)
    print(json.dumps(payload))
    return code, payload
