# Tool Version: V0.1 (from V0.0) | Overall improvement since last version: +40.0%
# Upgrade Summary: baseline score 3/5 -> 5/5; changes: added_validation_case, added_elapsed_ms_timing
import ast
import json
import os
from typing import Dict, List, Optional, Tuple

from tools.shared import read_text_file_with_fallback
import time

_EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".mypy_cache", ".pytest_cache",
}


def _iter_python_files(repo_path: str, max_files: Optional[int]) -> List[str]:
    files: List[str] = []
    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in _EXCLUDE_DIRS]
        for name in filenames:
            if not name.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(root, name), repo_path).replace("\\", "/")
            files.append(rel)
            if max_files is not None and len(files) >= max_files:
                return files
    return files


def _extract_imports(content: str, file_rel: str, repo_root: str) -> List[str]:
    """Return list of imported modules (as dotted names)."""
    imports: List[str] = []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def _module_to_rel_path(dotted: str, all_rel_paths: set) -> Optional[str]:
    """Try to map a dotted import name to a relative file path in repo."""
    as_path = dotted.replace(".", "/")
    candidates = [f"{as_path}.py", f"{as_path}/__init__.py"]
    for c in candidates:
        if c in all_rel_paths:
            return c
    return None


def run_dep_graph(repo_path: str, max_files: Optional[int] = None) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    py_files = _iter_python_files(repo_path, max_files)
    if not py_files:
        return 0, {
            "success": True,
            "dep_graph_mode": "python_imports",
            "files_scanned": 0,
            "edges": [],
            "importers": [],
            "importees": [],
            "summary": "No Python files found.",
        }

    all_paths_set = set(py_files)
    edges: List[Dict] = []
    importer_count: Dict[str, int] = {}
    importee_count: Dict[str, int] = {}
    truncated = max_files is not None and len(py_files) >= max_files

    for rel_path in py_files:
        full_path = os.path.join(repo_path, rel_path.replace("/", os.sep))
        content, _ = read_text_file_with_fallback(full_path)
        raw_imports = _extract_imports(content, rel_path, repo_path)
        for imp in raw_imports:
            target = _module_to_rel_path(imp, all_paths_set)
            if target and target != rel_path:
                edges.append({"from": rel_path, "to": target})
                importer_count[rel_path] = importer_count.get(rel_path, 0) + 1
                importee_count[target] = importee_count.get(target, 0) + 1

    top_importers = sorted(importer_count.items(), key=lambda x: -x[1])[:10]
    top_importees = sorted(importee_count.items(), key=lambda x: -x[1])[:10]

    payload = {
        "success": True,
        "dep_graph_mode": "python_imports",
        "files_scanned": len(py_files),
        "truncated": truncated,
        "edge_count": len(edges),
        "edges": edges[:200],
        "importers": [{"file": f, "import_count": c} for f, c in top_importers],
        "importees": [{"file": f, "imported_by_count": c} for f, c in top_importees],
        "summary": (
            f"Scanned {len(py_files)} Python files; "
            f"found {len(edges)} internal import edges; "
            f"most-imported: {top_importees[0][0] if top_importees else 'none'}."
        ),
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)

    return 0, payload


def cmd_dep_graph(repo_path: str, max_files: Optional[int] = None):
    code, payload = run_dep_graph(repo_path, max_files)
    print(json.dumps(payload))
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)

    return code, payload
