from __future__ import annotations

import ast
import configparser
import csv
import fnmatch
import json
import os
import py_compile
import re
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

try:
    import tomllib  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    tomllib = None

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

from tools.registry import TOOL_REGISTRY

_TEXT_FILE_EXTENSIONS = {
    ".py", ".json", ".yml", ".yaml", ".md", ".txt", ".cfg", ".ini", ".toml",
    ".env", ".csv", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".sh",
    ".ps1", ".bat", ".cmd", ".sql", ".xml", ".log",
}


def _safe_read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except OSError:
            return ""
    return ""


def _iter_files(repo: Path) -> Iterable[Path]:
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", ".mypy_cache", ".pytest_cache"}
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        root_path = Path(root)
        for file_name in files:
            if file_name.startswith(".") and file_name not in {".env", ".gitignore"}:
                continue
            yield root_path / file_name


def _rel(repo: Path, path: Path) -> str:
    return str(path.relative_to(repo)).replace("\\", "/")


def _matches_query(value: str, query: str | None) -> bool:
    if not query:
        return True
    return query.lower() in value.lower()


def _glob_locator(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    patterns = spec.get("patterns", [])
    matches: List[str] = []
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        if any(fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(rel, pattern) for pattern in patterns):
            if _matches_query(rel, query):
                matches.append(rel)
    matches.sort()
    return {"matches": matches[:limit], "count": len(matches), "patterns": patterns}


def _filename_matcher(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    needles = [n.lower() for n in spec.get("needles", [])]
    matches: List[str] = []
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        hay = path.name.lower()
        if any(needle in hay for needle in needles) and _matches_query(rel, query):
            matches.append(rel)
    matches.sort()
    return {"matches": matches[:limit], "count": len(matches), "needles": needles}


def _large_file_finder(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    items = []
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        try:
            items.append({"path": rel, "size_bytes": path.stat().st_size})
        except OSError:
            continue
    items.sort(key=lambda item: item["size_bytes"], reverse=True)
    return {"matches": items[:limit], "count": len(items)}


def _empty_dir_finder(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    matches = []
    for root, dirs, files in os.walk(repo):
        root_path = Path(root)
        rel = _rel(repo, root_path)
        if root_path == repo:
            continue
        if not dirs and not files and _matches_query(rel, query):
            matches.append(rel)
    matches.sort()
    return {"matches": matches[:limit], "count": len(matches)}


def _duplicate_name_finder(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    grouped: Dict[str, List[str]] = defaultdict(list)
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        if _matches_query(rel, query):
            grouped[path.name].append(rel)
    duplicates = [{"name": name, "paths": sorted(paths)} for name, paths in grouped.items() if len(paths) > 1]
    duplicates.sort(key=lambda item: (-len(item["paths"]), item["name"]))
    return {"matches": duplicates[:limit], "count": len(duplicates)}


def _extension_breakdown(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    counter = Counter()
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        if _matches_query(rel, query):
            counter[path.suffix.lower() or "<no_ext>"] += 1
    rows = [{"extension": ext, "count": count} for ext, count in counter.most_common(limit)]
    return {"matches": rows, "count": sum(counter.values())}


def _text_search(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    terms = spec.get("terms", [])
    matches = []
    for path in _iter_files(repo):
        if path.suffix.lower() not in _TEXT_FILE_EXTENSIONS:
            continue
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        text = _safe_read_text(path)
        for line_no, line in enumerate(text.splitlines(), start=1):
            if any(term.lower() in line.lower() for term in terms):
                matches.append({"path": rel, "line": line_no, "text": line.strip()[:160]})
                if len(matches) >= limit:
                    return {"matches": matches, "count": len(matches), "terms": terms}
    return {"matches": matches, "count": len(matches), "terms": terms}


def _parse_python_symbols(path: Path) -> Dict[str, List[str]]:
    text = _safe_read_text(path)
    result = {"imports": [], "classes": [], "functions": [], "docstring_nodes": 0}
    if not text:
        return result
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result["imports"].append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                result["imports"].append(f"{module}.{alias.name}" if module else alias.name)
        elif isinstance(node, ast.ClassDef):
            result["classes"].append(node.name)
            if ast.get_docstring(node):
                result["docstring_nodes"] += 1
        elif isinstance(node, ast.FunctionDef):
            result["functions"].append(node.name)
            if ast.get_docstring(node):
                result["docstring_nodes"] += 1
    return result


def _python_symbol_finder(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    mode = spec.get("symbol_mode", "functions")
    matches = []
    for path in _iter_files(repo):
        if path.suffix.lower() != ".py":
            continue
        rel = _rel(repo, path)
        symbols = _parse_python_symbols(path).get(mode, [])
        for symbol in symbols:
            if _matches_query(symbol, query) or _matches_query(rel, query):
                matches.append({"path": rel, "symbol": symbol})
    matches.sort(key=lambda item: (item["symbol"], item["path"]))
    return {"matches": matches[:limit], "count": len(matches), "symbol_mode": mode}


def _binary_file_locator(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    matches = []
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        try:
            chunk = path.read_bytes()[:512]
        except OSError:
            continue
        if b"\x00" in chunk:
            matches.append(rel)
    matches.sort()
    return {"matches": matches[:limit], "count": len(matches)}


def _long_path_finder(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    matches = []
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        if len(rel) > 120 and _matches_query(rel, query):
            matches.append({"path": rel, "length": len(rel)})
    matches.sort(key=lambda item: item["length"], reverse=True)
    return {"matches": matches[:limit], "count": len(matches)}


def _recent_file_finder(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    items = []
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        try:
            items.append({"path": rel, "mtime": path.stat().st_mtime})
        except OSError:
            continue
    items.sort(key=lambda item: item["mtime"], reverse=True)
    return {"matches": items[:limit], "count": len(items)}


def _planner_by_patterns(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    result = _glob_locator(repo, spec, query, limit)
    result["recommended_files"] = result.pop("matches")
    return result


def _filename_matcher_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    result = _filename_matcher(repo, spec, query, limit)
    result["recommended_files"] = result.pop("matches")
    return result


def _text_search_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    raw = _text_search(repo, spec, query, limit)
    files = []
    seen = set()
    for item in raw["matches"]:
        path = item["path"]
        if path in seen:
            continue
        seen.add(path)
        files.append(path)
    return {"recommended_files": files[:limit], "count": len(files), "terms": raw.get("terms", [])}


def _refactor_candidate_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    rows = _large_file_finder(repo, spec, query, limit * 3)["matches"]
    recommended = [row["path"] for row in rows if row["size_bytes"] > 8_000][:limit]
    return {"recommended_files": recommended, "count": len(recommended)}


def _doc_gap_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    code_dirs = Counter()
    doc_dirs = Counter()
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        parent = str(Path(rel).parent)
        if path.suffix.lower() in {".py", ".js", ".ts", ".tsx", ".jsx"}:
            code_dirs[parent] += 1
        if path.suffix.lower() == ".md":
            doc_dirs[parent] += 1
    rows = []
    for folder, code_count in code_dirs.items():
        if query and query.lower() not in folder.lower():
            continue
        doc_count = doc_dirs.get(folder, 0)
        if code_count >= 2 and doc_count == 0:
            rows.append({"folder": folder, "code_files": code_count, "doc_files": doc_count})
    rows.sort(key=lambda item: item["code_files"], reverse=True)
    return {"recommended_areas": rows[:limit], "count": len(rows)}


def _dead_code_review_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    rows = []
    for path in _iter_files(repo):
        if path.suffix.lower() != ".py":
            continue
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        text = _safe_read_text(path)
        if "if False:" in text or "TODO remove" in text or "deprecated" in text.lower():
            rows.append(rel)
    return {"recommended_files": rows[:limit], "count": len(rows)}


def _hotspot_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    rows = []
    now = time.time()
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        age_days = max(0.0, (now - stat.st_mtime) / 86400.0)
        score = stat.st_size / max(age_days + 1.0, 1.0)
        rows.append({"path": rel, "hotspot_score": round(score, 2)})
    rows.sort(key=lambda item: item["hotspot_score"], reverse=True)
    return {"recommended_files": rows[:limit], "count": len(rows)}


def _count_python_files(repo: Path) -> int:
    return sum(1 for path in _iter_files(repo) if path.suffix.lower() == ".py")


def _count_test_files(repo: Path) -> int:
    return sum(1 for path in _iter_files(repo) if fnmatch.fnmatch(path.name, "test_*.py") or fnmatch.fnmatch(path.name, "*_test.py"))


def _score_payload(name: str, score: int, details: Dict[str, Any]) -> Dict[str, Any]:
    rating = "strong" if score >= 80 else "good" if score >= 60 else "fair" if score >= 40 else "weak"
    return {"score": score, "rating": rating, **details}


def _score_python_file_count(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    count = _count_python_files(repo)
    score = min(100, 20 + min(count, 80))
    return _score_payload(spec["name"], score, {"python_file_count": count})


def _score_test_density(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    py_count = max(_count_python_files(repo), 1)
    test_count = _count_test_files(repo)
    ratio = test_count / py_count
    score = min(100, round(ratio * 200))
    return _score_payload(spec["name"], score, {"python_file_count": py_count, "test_file_count": test_count, "test_density": round(ratio, 3)})


def _score_docstring_coverage(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    total_nodes = 0
    doc_nodes = 0
    for path in _iter_files(repo):
        if path.suffix.lower() != ".py":
            continue
        symbols = _parse_python_symbols(path)
        total_nodes += len(symbols["classes"]) + len(symbols["functions"])
        doc_nodes += symbols["docstring_nodes"]
    coverage = doc_nodes / max(total_nodes, 1)
    score = round(coverage * 100)
    return _score_payload(spec["name"], score, {"documented_nodes": doc_nodes, "total_nodes": total_nodes, "coverage": round(coverage, 3)})


def _score_todo_density(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    todo_count = _text_search(repo, {"terms": ["TODO"]}, query, 10_000)["count"]
    file_count = max(sum(1 for _ in _iter_files(repo)), 1)
    density = todo_count / file_count
    score = max(0, 100 - round(density * 200))
    return _score_payload(spec["name"], score, {"todo_count": todo_count, "file_count": file_count, "todo_density": round(density, 3)})


def _score_config_sprawl(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    count = _filename_matcher(repo, {"needles": ["config", "settings", ".env", "package.json", "pyproject", "requirements"]}, query, 10_000)["count"]
    score = max(0, 100 - min(count * 3, 90))
    return _score_payload(spec["name"], score, {"config_file_count": count})


def _score_import_complexity(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    imports = set()
    per_file = []
    for path in _iter_files(repo):
        if path.suffix.lower() != ".py":
            continue
        symbols = _parse_python_symbols(path)
        imports.update(symbols["imports"])
        per_file.append(len(symbols["imports"]))
    avg = round(sum(per_file) / max(len(per_file), 1), 2)
    score = max(0, 100 - min(int(avg * 6), 90))
    return _score_payload(spec["name"], score, {"unique_imports": len(imports), "avg_imports_per_file": avg})


def _score_file_size_risk(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    large = _large_file_finder(repo, spec, query, 10_000)["matches"]
    risky = sum(1 for row in large if row["size_bytes"] > 20_000)
    score = max(0, 100 - risky * 5)
    return _score_payload(spec["name"], score, {"large_file_count": risky})


def _score_long_function_risk(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    long_functions = 0
    for path in _iter_files(repo):
        if path.suffix.lower() != ".py":
            continue
        text = _safe_read_text(path)
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and hasattr(node, "end_lineno") and node.end_lineno and node.lineno:
                if (node.end_lineno - node.lineno) > 60:
                    long_functions += 1
    score = max(0, 100 - long_functions * 4)
    return _score_payload(spec["name"], score, {"long_function_count": long_functions})


def _score_duplicate_name_risk(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    duplicates = _duplicate_name_finder(repo, spec, query, 10_000)["count"]
    score = max(0, 100 - duplicates * 8)
    return _score_payload(spec["name"], score, {"duplicate_name_count": duplicates})


def _score_repo_freshness(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    now = time.time()
    recent = 0
    total = 0
    for path in _iter_files(repo):
        total += 1
        try:
            if (now - path.stat().st_mtime) <= 30 * 86400:
                recent += 1
        except OSError:
            continue
    ratio = recent / max(total, 1)
    score = round(ratio * 100)
    return _score_payload(spec["name"], score, {"recent_files": recent, "total_files": total, "recent_ratio": round(ratio, 3)})


def _score_module_balance(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    counts = Counter(path.suffix.lower() or "<no_ext>" for path in _iter_files(repo))
    if not counts:
        return _score_payload(spec["name"], 0, {"extensions": []})
    values = list(counts.values())
    stdev = statistics.pstdev(values) if len(values) > 1 else 0.0
    score = max(0, 100 - int(stdev))
    return _score_payload(spec["name"], score, {"extensions": counts.most_common(limit), "stdev": round(stdev, 2)})


def _score_log_noise(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    log_files = sum(1 for path in _iter_files(repo) if path.suffix.lower() == ".log")
    score = max(0, 100 - log_files * 10)
    return _score_payload(spec["name"], score, {"log_file_count": log_files})


def _score_dependency_surface(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    imports = set()
    for path in _iter_files(repo):
        if path.suffix.lower() == ".py":
            imports.update(_parse_python_symbols(path)["imports"])
    score = max(0, 100 - min(len(imports), 100))
    return _score_payload(spec["name"], score, {"unique_imports": len(imports)})


def _boolean_check(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    check_name = spec.get("check_name")
    files = list(_iter_files(repo))
    if check_name == "tests_present":
        ok = any(fnmatch.fnmatch(path.name, "test_*.py") or fnmatch.fnmatch(path.name, "*_test.py") for path in files)
    elif check_name == "readme_present":
        ok = any("readme" in path.name.lower() for path in files)
    else:
        ok = any(path.stem.lower() in {"main", "app", "server", "manage"} for path in files)
    return {"passed": ok, "check_name": check_name}


def _parse_yaml_light(text: str) -> Dict[str, Any]:
    if yaml is not None:
        try:
            data = yaml.safe_load(text)
            if isinstance(data, dict):
                return {"type": "dict", "key_count": len(data), "keys": list(data.keys())[:20]}
            if isinstance(data, list):
                return {"type": "list", "item_count": len(data)}
            return {"type": type(data).__name__}
        except Exception:
            pass
    keys = []
    for line in text.splitlines():
        if re.match(r"^[A-Za-z0-9_.-]+:\s*", line):
            keys.append(line.split(":", 1)[0].strip())
    return {"type": "yaml_like", "key_count": len(keys), "keys": keys[:20]}


def _structured_validity_sampler(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    mode = spec.get("parse_mode")
    matches = []
    count = 0
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        if mode == "json" and path.suffix.lower() == ".json":
            count += 1
            try:
                json.loads(_safe_read_text(path))
                ok = True
                detail = "ok"
            except Exception as exc:
                ok = False
                detail = str(exc)
            matches.append({"path": rel, "ok": ok, "detail": detail})
        elif mode == "yaml" and path.suffix.lower() in {".yml", ".yaml"}:
            count += 1
            try:
                _parse_yaml_light(_safe_read_text(path))
                ok = True
                detail = "ok"
            except Exception as exc:
                ok = False
                detail = str(exc)
            matches.append({"path": rel, "ok": ok, "detail": detail})
        if len(matches) >= limit:
            break
    ok_count = sum(1 for row in matches if row["ok"])
    return {"matches": matches, "count": count, "ok_count": ok_count, "failure_count": len(matches) - ok_count}


def _python_syntax_sampler(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    matches = []
    scanned = 0
    for path in _iter_files(repo):
        if path.suffix.lower() != ".py":
            continue
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        scanned += 1
        try:
            ast.parse(_safe_read_text(path))
            ok = True
            detail = "ok"
        except SyntaxError as exc:
            ok = False
            detail = str(exc)
        matches.append({"path": rel, "ok": ok, "detail": detail})
        if len(matches) >= limit:
            break
    return {"matches": matches, "count": scanned, "failure_count": sum(1 for row in matches if not row["ok"])}


def _change_risk_snapshot(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    total_files = sum(1 for _ in _iter_files(repo))
    py_files = _count_python_files(repo)
    tests = _count_test_files(repo)
    todos = _text_search(repo, {"terms": ["TODO", "FIXME"]}, query, 10_000)["count"]
    large_files = _large_file_finder(repo, spec, query, 10_000)["matches"]
    risk_score = min(100, round((todos * 2) + max(len(large_files) - 10, 0) + max(py_files - tests, 0) * 0.5))
    return {"risk_score": risk_score, "total_files": total_files, "python_files": py_files, "test_files": tests, "todo_markers": todos, "large_file_count": len(large_files)}


def _structured_reader(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    mode = spec.get("read_mode")
    files = []
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        if mode == "json" and path.suffix.lower() == ".json":
            files.append(path)
        elif mode == "yaml" and path.suffix.lower() in {".yml", ".yaml"}:
            files.append(path)
        elif mode == "csv" and path.suffix.lower() == ".csv":
            files.append(path)
        elif mode == "text" and path.suffix.lower() in {".txt", ".log", ".md"}:
            files.append(path)
        elif mode == "markdown" and path.suffix.lower() == ".md":
            files.append(path)
        elif mode in {"python_symbols", "python_imports", "python_functions", "python_classes"} and path.suffix.lower() == ".py":
            files.append(path)
        elif mode == "env" and path.name.startswith(".env"):
            files.append(path)
        elif mode == "ini" and path.suffix.lower() in {".ini", ".cfg"}:
            files.append(path)
        elif mode == "toml" and path.suffix.lower() == ".toml":
            files.append(path)
        elif mode == "requirements" and "requirements" in path.name.lower() and path.suffix.lower() == ".txt":
            files.append(path)
        elif mode == "changelog" and "changelog" in path.name.lower():
            files.append(path)
        elif mode == "license" and path.name.lower().startswith("license"):
            files.append(path)
        elif mode == "dockerfile" and path.name.lower() == "dockerfile":
            files.append(path)
        elif mode == "compose" and "compose" in path.name.lower() and path.suffix.lower() in {".yml", ".yaml"}:
            files.append(path)
        elif mode == "package_json" and path.name == "package.json":
            files.append(path)
        elif mode == "notebook" and path.suffix.lower() == ".ipynb":
            files.append(path)
        elif mode == "log" and path.suffix.lower() == ".log":
            files.append(path)

    rows = []
    for path in files[:limit]:
        rel = _rel(repo, path)
        text = _safe_read_text(path)
        if mode == "json":
            try:
                data = json.loads(text)
                summary = {"path": rel, "type": type(data).__name__, "key_count": len(data) if isinstance(data, dict) else None}
            except Exception as exc:
                summary = {"path": rel, "error": str(exc)}
        elif mode == "yaml":
            summary = {"path": rel, **_parse_yaml_light(text)}
        elif mode == "csv":
            reader = list(csv.reader(text.splitlines())) if text else []
            summary = {"path": rel, "row_count": max(len(reader) - 1, 0), "column_count": len(reader[0]) if reader else 0}
        elif mode == "text":
            summary = {"path": rel, "preview": text[:200], "line_count": len(text.splitlines())}
        elif mode == "markdown":
            headings = [line.strip() for line in text.splitlines() if line.lstrip().startswith("#")][:20]
            summary = {"path": rel, "headings": headings, "heading_count": len(headings)}
        elif mode == "python_symbols":
            symbols = _parse_python_symbols(path)
            summary = {"path": rel, "imports": symbols["imports"][:20], "functions": symbols["functions"][:20], "classes": symbols["classes"][:20]}
        elif mode == "python_imports":
            summary = {"path": rel, "imports": _parse_python_symbols(path)["imports"][:30]}
        elif mode == "python_functions":
            summary = {"path": rel, "functions": _parse_python_symbols(path)["functions"][:30]}
        elif mode == "python_classes":
            summary = {"path": rel, "classes": _parse_python_symbols(path)["classes"][:30]}
        elif mode == "env":
            keys = [line.split("=", 1)[0].strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#") and "=" in line]
            summary = {"path": rel, "keys": keys[:30], "key_count": len(keys)}
        elif mode == "ini":
            parser = configparser.ConfigParser()
            parser.read_string(text)
            summary = {"path": rel, "sections": parser.sections(), "section_count": len(parser.sections())}
        elif mode == "toml":
            if tomllib is not None:
                data = tomllib.loads(text)
                summary = {"path": rel, "keys": list(data.keys())[:30], "key_count": len(data.keys())}
            else:
                summary = {"path": rel, "preview": text[:200]}
        elif mode == "requirements":
            deps = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
            summary = {"path": rel, "dependencies": deps[:30], "dependency_count": len(deps)}
        elif mode == "changelog":
            summary = {"path": rel, "preview": text[:300], "line_count": len(text.splitlines())}
        elif mode == "license":
            summary = {"path": rel, "preview": text[:200]}
        elif mode == "dockerfile":
            cmds = [line.split()[0] for line in text.splitlines() if line.strip() and not line.strip().startswith("#")][:30]
            summary = {"path": rel, "instructions": cmds, "instruction_count": len(cmds)}
        elif mode == "compose":
            summary = {"path": rel, **_parse_yaml_light(text)}
        elif mode == "package_json":
            try:
                data = json.loads(text)
                summary = {"path": rel, "name": data.get("name"), "scripts": sorted((data.get("scripts") or {}).keys()), "dependency_count": len((data.get("dependencies") or {}))}
            except Exception as exc:
                summary = {"path": rel, "error": str(exc)}
        elif mode == "notebook":
            try:
                data = json.loads(text)
                cells = data.get("cells", [])
                summary = {"path": rel, "cell_count": len(cells), "code_cells": sum(1 for c in cells if c.get("cell_type") == "code")}
            except Exception as exc:
                summary = {"path": rel, "error": str(exc)}
        else:
            errors = sum(1 for line in text.splitlines() if "error" in line.lower())
            warnings = sum(1 for line in text.splitlines() if "warn" in line.lower())
            summary = {"path": rel, "line_count": len(text.splitlines()), "error_lines": errors, "warning_lines": warnings}
        rows.append(summary)
    return {"matches": rows, "count": len(files), "read_mode": mode}


def _execution_probe(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    mode = spec.get("probe_mode")
    matches = []
    scanned = 0
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        if mode == "python_compile" and path.suffix.lower() == ".py":
            scanned += 1
            try:
                py_compile.compile(str(path), doraise=True)
                matches.append({"path": rel, "ok": True})
            except Exception as exc:
                matches.append({"path": rel, "ok": False, "detail": str(exc)})
        elif mode == "pytest_collection" and path.suffix.lower() == ".py":
            text = _safe_read_text(path)
            tests = re.findall(r"^def\s+(test_[A-Za-z0-9_]+)", text, flags=re.MULTILINE)
            if tests:
                scanned += 1
                matches.append({"path": rel, "tests": tests[:20], "test_count": len(tests)})
        elif mode == "script_entrypoints" and path.suffix.lower() == ".py":
            text = _safe_read_text(path)
            if 'if __name__ == "__main__"' in text or "if __name__ == '__main__'" in text:
                scanned += 1
                matches.append({"path": rel, "has_entrypoint": True})
        elif mode == "module_resolution" and path.suffix.lower() == ".py":
            scanned += 1
            matches.append({"path": rel, "module_name": rel[:-3].replace('/', '.')})
        elif mode == "json_parse" and path.suffix.lower() == ".json":
            scanned += 1
            try:
                json.loads(_safe_read_text(path))
                matches.append({"path": rel, "ok": True})
            except Exception as exc:
                matches.append({"path": rel, "ok": False, "detail": str(exc)})
        elif mode == "yaml_parse" and path.suffix.lower() in {".yml", ".yaml"}:
            scanned += 1
            try:
                _parse_yaml_light(_safe_read_text(path))
                matches.append({"path": rel, "ok": True})
            except Exception as exc:
                matches.append({"path": rel, "ok": False, "detail": str(exc)})
        elif mode == "command_catalog" and path == repo:
            pass
        elif mode == "notebook_parse" and path.suffix.lower() == ".ipynb":
            scanned += 1
            try:
                data = json.loads(_safe_read_text(path))
                matches.append({"path": rel, "ok": True, "cell_count": len(data.get("cells", []))})
            except Exception as exc:
                matches.append({"path": rel, "ok": False, "detail": str(exc)})
        elif mode == "shell_scripts" and path.suffix.lower() in {".sh", ".ps1", ".bat", ".cmd"}:
            scanned += 1
            matches.append({"path": rel, "size_bytes": path.stat().st_size})
        elif mode == "python_entrypoints" and path.name.lower() in {"main.py", "app.py", "server.py", "manage.py"}:
            scanned += 1
            matches.append({"path": rel, "exists": True})
        if len(matches) >= limit:
            break

    if mode == "command_catalog":
        visible = sorted(TOOL_REGISTRY.keys())
        return {"matches": visible[:limit], "count": len(visible), "probe_mode": mode}

    return {"matches": matches[:limit], "count": scanned, "probe_mode": mode}


def _health_scan(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    mode = spec.get("scan_mode")
    matches = []
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        try:
            if mode == "missing_readme":
                # top-level project dirs under repo missing README
                continue
            elif mode == "missing_init":
                if path.suffix.lower() == ".py":
                    parent = path.parent
                    if any(child.suffix.lower() == ".py" for child in parent.iterdir()) and not (parent / "__init__.py").exists():
                        matches.append(str(parent.relative_to(repo)).replace("\\", "/"))
            elif mode == "trailing_whitespace":
                text = _safe_read_text(path)
                for line_no, line in enumerate(text.splitlines(), start=1):
                    if line.rstrip() != line:
                        matches.append({"path": rel, "line": line_no})
                        break
            elif mode == "large_logs":
                if path.suffix.lower() == ".log" and path.stat().st_size > 100_000:
                    matches.append({"path": rel, "size_bytes": path.stat().st_size})
            elif mode == "hardcoded_secrets":
                text = _safe_read_text(path)
                if re.search(r"(api[_-]?key|secret|token|password)\s*=\s*['\"][^'\"]+['\"]", text, flags=re.IGNORECASE):
                    matches.append(rel)
            elif mode == "debug_statements":
                text = _safe_read_text(path)
                if "print(" in text or "breakpoint(" in text or "pdb.set_trace" in text:
                    matches.append(rel)
            elif mode == "empty_files":
                if path.stat().st_size == 0:
                    matches.append(rel)
            elif mode == "line_length":
                text = _safe_read_text(path)
                long_lines = [i for i, line in enumerate(text.splitlines(), start=1) if len(line) > 120]
                if long_lines:
                    matches.append({"path": rel, "lines": long_lines[:10]})
            elif mode == "tab_indent":
                text = _safe_read_text(path)
                if any(line.startswith("\t") for line in text.splitlines()):
                    matches.append(rel)
            elif mode == "mixed_newlines":
                raw = path.read_bytes()
                if b"\r\n" in raw and b"\n" in raw.replace(b"\r\n", b""):
                    matches.append(rel)
            elif mode == "broken_symlinks":
                if path.is_symlink() and not path.exists():
                    matches.append(rel)
            elif mode == "virtualenv_leak":
                if any(part.lower() in {".venv", "venv", "env"} for part in path.parts):
                    matches.append(rel)
            elif mode == "temp_files":
                if path.name.endswith(("~", ".tmp", ".bak", ".swp", ".swo")):
                    matches.append(rel)
            elif mode == "cache_dirs":
                if any(part == "__pycache__" for part in path.parts):
                    matches.append(rel)
            elif mode == "duplicate_test_names" and path.suffix.lower() == ".py":
                tests = re.findall(r"^def\s+(test_[A-Za-z0-9_]+)", _safe_read_text(path), flags=re.MULTILINE)
                dupes = [name for name, count in Counter(tests).items() if count > 1]
                if dupes:
                    matches.append({"path": rel, "duplicate_tests": dupes})
        except Exception:
            continue
        if len(matches) >= limit:
            break

    if mode == "missing_readme":
        projects = []
        for child in repo.iterdir():
            if child.is_dir() and child.name not in {".git", "node_modules", "__pycache__"}:
                has_readme = any(grand.name.lower().startswith("readme") for grand in child.iterdir() if grand.is_file())
                if not has_readme and _matches_query(child.name, query):
                    projects.append(child.name)
        matches = projects[:limit]

    if mode == "cache_dirs":
        matches = sorted(set(matches))[:limit]
    if mode == "missing_init":
        matches = sorted(set(matches))[:limit]
    return {"matches": matches, "count": len(matches), "scan_mode": mode}


def _query_matched_files(repo: Path, query: str | None) -> List[Path]:
    files = []
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        if _matches_query(rel, query):
            files.append(path)
            continue
        if query and path.suffix.lower() in _TEXT_FILE_EXTENSIONS:
            text = _safe_read_text(path)
            if query.lower() in text.lower():
                files.append(path)
    return files


def _classify_config_kind(path: Path) -> str:
    if path.name.startswith(".env"):
        return "env"
    if path.suffix.lower() == ".json":
        return "json"
    if path.suffix.lower() in {".yml", ".yaml"}:
        return "yaml"
    if path.suffix.lower() == ".toml":
        return "toml"
    if path.suffix.lower() in {".ini", ".cfg"}:
        return "ini"
    return "other"


def _config_review_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    base = _planner_by_patterns(repo, spec, query, limit * 3)
    files = base.get("recommended_files", [])
    typed = Counter(_classify_config_kind(Path(path)) for path in files)
    flagged = [path for path in files if any(token in path.lower() for token in ("secret", ".env", "prod", "config"))][:limit]
    return {
        "recommended_files": files[:limit],
        "config_types": dict(typed),
        "flagged_files": flagged,
        "count": len(files),
    }


def _dependency_cleanup_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    candidates = _planner_by_patterns(repo, spec, query, limit * 3).get("recommended_files", [])
    details = []
    for rel in candidates[:limit]:
        text = _safe_read_text(repo / rel)
        deps = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
        details.append({"path": rel, "dependency_count": len(deps), "sample": deps[:10]})
    return {"recommended_files": candidates[:limit], "details": details, "count": len(candidates)}


def _logging_improvement_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    rows = []
    for path in _iter_files(repo):
        if path.suffix.lower() not in {".py", ".js", ".ts", ".tsx", ".jsx"}:
            continue
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        text = _safe_read_text(path)
        print_calls = text.count("print(")
        logging_calls = text.count("logging.") + text.count("logger.")
        if print_calls or logging_calls:
            rows.append({"path": rel, "print_calls": print_calls, "logging_calls": logging_calls, "priority": (print_calls * 2) + logging_calls})
    rows.sort(key=lambda item: item["priority"], reverse=True)
    return {"recommended_files": rows[:limit], "count": len(rows)}


def _error_handling_review_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    rows = []
    for path in _iter_files(repo):
        if path.suffix.lower() != ".py":
            continue
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        text = _safe_read_text(path)
        try_count = len(re.findall(r"\btry:\s*$", text, flags=re.MULTILINE))
        except_count = len(re.findall(r"\bexcept\b", text))
        bare_except = len(re.findall(r"except\s*:\s*$", text, flags=re.MULTILINE))
        raise_count = len(re.findall(r"\braise\b", text))
        if try_count or except_count or raise_count:
            rows.append({"path": rel, "try_blocks": try_count, "except_blocks": except_count, "bare_except": bare_except, "raise_count": raise_count})
    rows.sort(key=lambda item: (item["bare_except"], item["except_blocks"], item["try_blocks"]), reverse=True)
    return {"recommended_files": rows[:limit], "count": len(rows)}


def _model_layer_review_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    rows = []
    for rel in _filename_matcher_planner(repo, spec, query, limit * 3).get("recommended_files", []):
        text = _safe_read_text(repo / rel)
        rows.append({
            "path": rel,
            "dataclass_hits": text.count("@dataclass"),
            "pydantic_hits": text.lower().count("basemodel"),
            "orm_hits": sum(text.lower().count(token) for token in ["column(", "relationship(", "foreignkey("]),
        })
    rows.sort(key=lambda item: (item["dataclass_hits"] + item["pydantic_hits"] + item["orm_hits"]), reverse=True)
    return {"recommended_files": rows[:limit], "count": len(rows)}


def _auth_review_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    rows = []
    for rel in _filename_matcher_planner(repo, spec, query, limit * 3).get("recommended_files", []):
        text = _safe_read_text(repo / rel)
        rows.append({
            "path": rel,
            "token_mentions": len(re.findall(r"token|jwt|oauth|session", text, flags=re.IGNORECASE)),
            "secret_mentions": len(re.findall(r"secret|password|credential", text, flags=re.IGNORECASE)),
        })
    rows.sort(key=lambda item: (item["secret_mentions"], item["token_mentions"]), reverse=True)
    return {"recommended_files": rows[:limit], "count": len(rows)}


def _api_surface_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    rows = []
    for rel in _filename_matcher_planner(repo, spec, query, limit * 3).get("recommended_files", []):
        text = _safe_read_text(repo / rel)
        route_hits = len(re.findall(r"@.*route|@app\.(get|post|put|delete|patch)|router\.", text, flags=re.IGNORECASE))
        http_verbs = len(re.findall(r"\b(GET|POST|PUT|DELETE|PATCH)\b", text, flags=re.IGNORECASE))
        rows.append({"path": rel, "route_hits": route_hits, "http_verb_mentions": http_verbs})
    rows.sort(key=lambda item: (item["route_hits"], item["http_verb_mentions"]), reverse=True)
    return {"recommended_files": rows[:limit], "count": len(rows)}


def _frontend_review_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    files = _planner_by_patterns(repo, spec, query, limit * 4).get("recommended_files", [])
    rows = []
    for rel in files:
        text = _safe_read_text(repo / rel)
        rows.append({
            "path": rel,
            "extension": Path(rel).suffix.lower(),
            "react_signals": sum(text.count(token) for token in ["useState", "useEffect", "jsx", "tsx"]),
            "network_signals": sum(text.count(token) for token in ["fetch(", "axios", "useQuery", "useSWR"]),
        })
    rows.sort(key=lambda item: (item["react_signals"], item["network_signals"]), reverse=True)
    return {"recommended_files": rows[:limit], "count": len(rows)}


def _migration_risk_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    files = _filename_matcher_planner(repo, spec, query, limit * 4).get("recommended_files", [])
    rows = []
    for rel in files:
        text = _safe_read_text(repo / rel)
        destructive = len(re.findall(r"drop\s+table|drop\s+column|alter\s+table|rename\s+column", text, flags=re.IGNORECASE))
        rows.append({"path": rel, "destructive_signals": destructive, "line_count": len(text.splitlines())})
    rows.sort(key=lambda item: (item["destructive_signals"], item["line_count"]), reverse=True)
    return {"recommended_files": rows[:limit], "count": len(rows)}


def _hotspot_review_planner_plus(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    rows = []
    now = time.time()
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        if path.suffix.lower() not in _TEXT_FILE_EXTENSIONS:
            continue
        text = _safe_read_text(path)
        try:
            stat = path.stat()
        except OSError:
            continue
        age_days = max(1.0, (now - stat.st_mtime) / 86400.0)
        todo_count = len(re.findall(r"TODO|FIXME", text))
        debug_count = text.count("print(") + text.count("breakpoint(")
        score = round((stat.st_size / 512.0) + (todo_count * 8) + (debug_count * 10) + (30 / age_days), 2)
        rows.append({"path": rel, "hotspot_score": score, "todo_count": todo_count, "debug_count": debug_count, "size_bytes": stat.st_size})
    rows.sort(key=lambda item: item["hotspot_score"], reverse=True)
    return {"recommended_files": rows[:limit], "count": len(rows)}


def _score_config_sprawl_plus(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    files = _filename_matcher(repo, {"needles": ["config", "settings", ".env", "package.json", "pyproject", "requirements"]}, query, 10_000)["matches"]
    dir_count = len({str(Path(path).parent) for path in files})
    basename_dupes = len([name for name, count in Counter(Path(path).name for path in files).items() if count > 1])
    score = max(0, 100 - min((len(files) * 2) + (dir_count * 2) + (basename_dupes * 5), 95))
    return _score_payload(spec["name"], score, {"config_file_count": len(files), "config_dir_count": dir_count, "duplicate_config_names": basename_dupes, "sample_files": files[:limit]})


def _score_import_complexity_plus(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    imports = set()
    per_file = []
    heaviest = []
    for path in _iter_files(repo):
        if path.suffix.lower() != ".py":
            continue
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        file_imports = _parse_python_symbols(path)["imports"]
        imports.update(file_imports)
        per_file.append(len(file_imports))
        heaviest.append({"path": rel, "import_count": len(file_imports)})
    heaviest.sort(key=lambda item: item["import_count"], reverse=True)
    avg = round(sum(per_file) / max(len(per_file), 1), 2)
    score = max(0, 100 - min(int(avg * 5) + len(imports) // 8, 95))
    return _score_payload(spec["name"], score, {"unique_imports": len(imports), "avg_imports_per_file": avg, "heaviest_files": heaviest[:limit]})


def _score_file_size_risk_plus(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    rows = _large_file_finder(repo, spec, query, 10_000)["matches"]
    thresholds = {"over_10k": 0, "over_25k": 0, "over_50k": 0}
    for row in rows:
        size = row["size_bytes"]
        if size > 10_000:
            thresholds["over_10k"] += 1
        if size > 25_000:
            thresholds["over_25k"] += 1
        if size > 50_000:
            thresholds["over_50k"] += 1
    score = max(0, 100 - min(thresholds["over_10k"] + (thresholds["over_25k"] * 2) + (thresholds["over_50k"] * 4), 95))
    return _score_payload(spec["name"], score, {"thresholds": thresholds, "largest_files": rows[:limit]})


def _score_long_function_risk_plus(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    rows = []
    for path in _iter_files(repo):
        if path.suffix.lower() != ".py":
            continue
        rel = _rel(repo, path)
        text = _safe_read_text(path)
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and hasattr(node, "end_lineno") and node.end_lineno and node.lineno:
                length = node.end_lineno - node.lineno
                if length > 40:
                    rows.append({"path": rel, "function": node.name, "length": length})
    rows.sort(key=lambda item: item["length"], reverse=True)
    score = max(0, 100 - min(len(rows) * 3, 95))
    return _score_payload(spec["name"], score, {"long_function_count": len(rows), "top_long_functions": rows[:limit]})


def _score_duplicate_name_risk_plus(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    rows = _duplicate_name_finder(repo, spec, query, 10_000)["matches"]
    score = max(0, 100 - min(sum(len(row["paths"]) - 1 for row in rows) * 6, 95))
    return _score_payload(spec["name"], score, {"duplicate_groups": rows[:limit], "duplicate_group_count": len(rows)})


def _score_module_balance_plus(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    counts = Counter(path.suffix.lower() or "<no_ext>" for path in _iter_files(repo))
    total = sum(counts.values()) or 1
    probs = [count / total for count in counts.values()]
    entropy = -sum(p * (0 if p == 0 else __import__("math").log2(p)) for p in probs)
    score = min(100, round(entropy * 20))
    return _score_payload(spec["name"], score, {"extensions": counts.most_common(limit), "entropy": round(entropy, 3), "extension_count": len(counts)})


def _score_dependency_surface_plus(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    imported = set()
    declared = set()
    for path in _iter_files(repo):
        rel = _rel(repo, path)
        if path.suffix.lower() == ".py":
            imported.update(name.split(".", 1)[0] for name in _parse_python_symbols(path)["imports"])
        elif "requirements" in path.name.lower() and path.suffix.lower() == ".txt":
            for line in _safe_read_text(path).splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    declared.add(re.split(r"[<>=!~]", line)[0].strip())
    undeclared = sorted(imported - declared)[:limit]
    score = max(0, 100 - min((len(imported) // 2) + len(undeclared), 95))
    return _score_payload(spec["name"], score, {"imported_top_level_modules": len(imported), "declared_dependencies": len(declared), "undeclared_sample": undeclared})


def _change_risk_snapshot_plus(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    hotspots = _hotspot_review_planner_plus(repo, spec, query, limit).get("recommended_files", [])
    long_funcs = _score_long_function_risk_plus(repo, spec, query, limit).get("top_long_functions", [])
    duplicate_groups = _duplicate_name_finder(repo, spec, query, limit).get("matches", [])
    todo_count = _text_search(repo, {"terms": ["TODO", "FIXME"]}, query, 10_000)["count"]
    risk_score = min(100, round((todo_count * 1.5) + (len(hotspots) * 3) + (len(long_funcs) * 2) + (len(duplicate_groups) * 4)))
    return {
        "risk_score": risk_score,
        "top_hotspots": hotspots[:limit],
        "long_functions": long_funcs[:limit],
        "duplicate_name_groups": duplicate_groups[:limit],
        "todo_markers": todo_count,
    }


def _json_summary_reader_plus(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    rows = _structured_reader(repo, {**spec, "read_mode": "json"}, query, limit).get("matches", [])
    key_counter = Counter()
    for row in rows:
        rel = row.get("path")
        if not rel or row.get("error"):
            continue
        try:
            data = json.loads(_safe_read_text(repo / rel))
        except Exception:
            continue
        if isinstance(data, dict):
            key_counter.update(data.keys())
    return {"matches": rows, "count": len(rows), "top_keys": key_counter.most_common(15), "read_mode": "json"}


def _requirements_reader_plus(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    files = []
    packages = Counter()
    versioned = []
    for path in _iter_files(repo):
        if "requirements" not in path.name.lower() or path.suffix.lower() != ".txt":
            continue
        rel = _rel(repo, path)
        if not _matches_query(rel, query):
            continue
        deps = []
        for line in _safe_read_text(path).splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name = re.split(r"[<>=!~]", line)[0].strip()
            deps.append(line)
            packages[name] += 1
            if any(op in line for op in ["==", ">=", "<=", "~="]):
                versioned.append(line)
        files.append({"path": rel, "dependencies": deps[:30], "dependency_count": len(deps)})
    duplicates = [{"package": name, "occurrences": count} for name, count in packages.items() if count > 1]
    duplicates.sort(key=lambda item: item["occurrences"], reverse=True)
    return {"matches": files[:limit], "count": len(files), "duplicate_packages": duplicates[:limit], "version_pinned_count": len(versioned)}


def _query_locator(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    files = [_rel(repo, path) for path in _query_matched_files(repo, query)]
    files.sort()
    return {"matches": files[:limit], "count": len(files), "query_mode": "locator"}


def _query_planner(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    files = [_rel(repo, path) for path in _query_matched_files(repo, query)]
    prioritized = sorted(files, key=lambda item: ("readme" not in item.lower(), item))
    return {"recommended_files": prioritized[:limit], "count": len(prioritized), "query_mode": "planner"}


def _query_risk_score(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    files = _query_matched_files(repo, query)
    todo_hits = 0
    large_hits = 0
    for path in files:
        text = _safe_read_text(path)
        todo_hits += len(re.findall(r"TODO|FIXME", text))
        try:
            if path.stat().st_size > 20_000:
                large_hits += 1
        except OSError:
            continue
    score = min(100, todo_hits * 5 + large_hits * 7 + len(files))
    return {"score": score, "rating": "strong" if score < 25 else "good" if score < 50 else "fair" if score < 75 else "weak", "matched_files": len(files), "todo_hits": todo_hits, "large_file_hits": large_hits}


def _query_excerpt_reader(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    matches = []
    if not query:
        return {"matches": matches, "count": 0, "query_mode": "excerpt_reader"}
    for path in _query_matched_files(repo, query):
        if path.suffix.lower() not in _TEXT_FILE_EXTENSIONS:
            continue
        rel = _rel(repo, path)
        for line_no, line in enumerate(_safe_read_text(path).splitlines(), start=1):
            if query.lower() in line.lower():
                matches.append({"path": rel, "line": line_no, "text": line.strip()[:200]})
                if len(matches) >= limit:
                    return {"matches": matches, "count": len(matches), "query_mode": "excerpt_reader"}
    return {"matches": matches, "count": len(matches), "query_mode": "excerpt_reader"}


def _query_parse_probe(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    matches = []
    for path in _query_matched_files(repo, query):
        rel = _rel(repo, path)
        if path.suffix.lower() == ".py":
            try:
                ast.parse(_safe_read_text(path))
                matches.append({"path": rel, "ok": True, "mode": "python"})
            except SyntaxError as exc:
                matches.append({"path": rel, "ok": False, "mode": "python", "detail": str(exc)})
        elif path.suffix.lower() == ".json":
            try:
                json.loads(_safe_read_text(path))
                matches.append({"path": rel, "ok": True, "mode": "json"})
            except Exception as exc:
                matches.append({"path": rel, "ok": False, "mode": "json", "detail": str(exc)})
        if len(matches) >= limit:
            break
    return {"matches": matches, "count": len(matches), "probe_mode": "query_parse"}


def _query_health_scan(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    matches = []
    for path in _query_matched_files(repo, query):
        rel = _rel(repo, path)
        text = _safe_read_text(path)
        issues = []
        if any(line.rstrip() != line for line in text.splitlines()):
            issues.append("trailing_whitespace")
        if any(len(line) > 120 for line in text.splitlines()):
            issues.append("long_lines")
        if path.name.endswith((".tmp", ".bak", "~")):
            issues.append("temp_file")
        if issues:
            matches.append({"path": rel, "issues": issues})
        if len(matches) >= limit:
            break
    return {"matches": matches, "count": len(matches), "scan_mode": "query_health"}


def _query_network_probe(repo: Path, spec: Dict[str, Any], query: str | None, limit: int) -> Dict[str, Any]:
    files = _query_matched_files(repo, query)
    endpoints = []
    for path in files:
        if path.suffix.lower() not in _TEXT_FILE_EXTENSIONS:
            continue
        rel = _rel(repo, path)
        text = _safe_read_text(path)
        urls = re.findall(r"https?://[^\s'\"\)>]+", text)
        hosts = re.findall(r"\b([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b", text)
        if urls or hosts:
            endpoints.append({
                "path": rel,
                "url_sample": sorted(set(urls))[:5],
                "host_sample": sorted(set(hosts))[:8],
                "url_count": len(urls),
            })
        if len(endpoints) >= limit:
            break
    return {"matches": endpoints, "count": len(endpoints), "probe_mode": "query_network"}


_HANDLER_MAP = {
    "glob_locator": _glob_locator,
    "filename_matcher": _filename_matcher,
    "large_file_finder": _large_file_finder,
    "empty_dir_finder": _empty_dir_finder,
    "duplicate_name_finder": _duplicate_name_finder,
    "extension_breakdown": _extension_breakdown,
    "text_search": _text_search,
    "python_symbol_finder": _python_symbol_finder,
    "binary_file_locator": _binary_file_locator,
    "long_path_finder": _long_path_finder,
    "recent_file_finder": _recent_file_finder,
    "planner_by_patterns": _planner_by_patterns,
    "filename_matcher_planner": _filename_matcher_planner,
    "text_search_planner": _text_search_planner,
    "refactor_candidate_planner": _refactor_candidate_planner,
    "doc_gap_planner": _doc_gap_planner,
    "dead_code_review_planner": _dead_code_review_planner,
    "hotspot_planner": _hotspot_planner,
    "config_review_planner": _config_review_planner,
    "dependency_cleanup_planner": _dependency_cleanup_planner,
    "logging_improvement_planner": _logging_improvement_planner,
    "error_handling_review_planner": _error_handling_review_planner,
    "model_layer_review_planner": _model_layer_review_planner,
    "auth_review_planner": _auth_review_planner,
    "api_surface_planner": _api_surface_planner,
    "frontend_review_planner": _frontend_review_planner,
    "migration_risk_planner": _migration_risk_planner,
    "hotspot_review_planner_plus": _hotspot_review_planner_plus,
    "score_python_file_count": _score_python_file_count,
    "score_test_density": _score_test_density,
    "score_docstring_coverage": _score_docstring_coverage,
    "score_todo_density": _score_todo_density,
    "score_config_sprawl": _score_config_sprawl,
    "score_import_complexity": _score_import_complexity,
    "score_file_size_risk": _score_file_size_risk,
    "score_long_function_risk": _score_long_function_risk,
    "score_duplicate_name_risk": _score_duplicate_name_risk,
    "score_repo_freshness": _score_repo_freshness,
    "score_module_balance": _score_module_balance,
    "score_log_noise": _score_log_noise,
    "score_dependency_surface": _score_dependency_surface,
    "score_config_sprawl_plus": _score_config_sprawl_plus,
    "score_import_complexity_plus": _score_import_complexity_plus,
    "score_file_size_risk_plus": _score_file_size_risk_plus,
    "score_long_function_risk_plus": _score_long_function_risk_plus,
    "score_duplicate_name_risk_plus": _score_duplicate_name_risk_plus,
    "score_module_balance_plus": _score_module_balance_plus,
    "score_dependency_surface_plus": _score_dependency_surface_plus,
    "boolean_check": _boolean_check,
    "structured_validity_sampler": _structured_validity_sampler,
    "python_syntax_sampler": _python_syntax_sampler,
    "change_risk_snapshot": _change_risk_snapshot,
    "change_risk_snapshot_plus": _change_risk_snapshot_plus,
    "structured_reader": _structured_reader,
    "json_summary_reader_plus": _json_summary_reader_plus,
    "requirements_reader_plus": _requirements_reader_plus,
    "execution_probe": _execution_probe,
    "health_scan": _health_scan,
    "query_locator": _query_locator,
    "query_planner": _query_planner,
    "query_risk_score": _query_risk_score,
    "query_excerpt_reader": _query_excerpt_reader,
    "query_parse_probe": _query_parse_probe,
    "query_health_scan": _query_health_scan,
    "query_network_probe": _query_network_probe,
}


def run_catalog_tool(repo_path: str, spec: Dict[str, Any], query: str | None = None, limit: int = 50) -> Tuple[int, Dict[str, Any]]:
    t0 = time.monotonic()
    repo = Path(repo_path)
    if not repo.exists():
        return 2, {"success": False, "error": "missing_repo", "detail": str(repo)}

    handler_name = spec.get("handler")
    handler = _HANDLER_MAP.get(handler_name)
    if handler is None:
        return 2, {"success": False, "error": "unknown_handler", "handler": handler_name, "tool": spec.get("name")}

    try:
        result = handler(repo, spec, query, max(1, int(limit)))
    except Exception as exc:
        return 1, {
            "success": False,
            "tool": spec.get("name"),
            "category": spec.get("category"),
            "handler": handler_name,
            "error": "tool_runtime_error",
            "detail": str(exc),
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }

    payload: Dict[str, Any] = {
        "success": True,
        "tool": spec.get("name"),
        "category": spec.get("category"),
        "handler": handler_name,
        "query": query,
        "limit": limit,
        **result,
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
        "summary": f"{spec.get('name')} completed using handler '{handler_name}'.",
    }
    return 0, payload
