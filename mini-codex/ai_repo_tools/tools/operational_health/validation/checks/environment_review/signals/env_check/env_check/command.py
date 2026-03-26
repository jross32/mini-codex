# Tool Version: V2.7 (from V2.6) | Overall improvement since last version: +0.0%
# Upgrade Summary: baseline score 4/5 -> 4/5; changes: no structural patches
import importlib.util
import json
import os
import re
import sys


# ── dependency-file discovery priority ───────────────────────────────────────
# Checked in order; first file found wins.
_DEP_FILES = [
    "requirements.txt",
    "requirements-dev.txt",
    "requirements_dev.txt",
    "pyproject.toml",
]


# ── requirements.txt parser ───────────────────────────────────────────────────
# Recognises lines like:
#   flask>=2.0
#   requests==2.28.0
#   pytest; python_version >= "3.8"
#   -r other.txt           (skipped — recursive includes)
#   # comment              (skipped)
#   git+https://...        (skipped — VCS deps)

_VCS_RE = re.compile(r"^(git|hg|svn|bzr)\+", re.I)
_EXTRA_RE = re.compile(r"\[.*?\]")            # strip extras: pkg[security]
_MARKER_RE = re.compile(r";.*$")             # strip env markers: pkg; python_version>= ...
_SPECIFIER_RE = re.compile(r"[><=!~^][^\s]*") # strip version specifiers: >=2, ==1.0

def _parse_requirements_txt(path: str) -> tuple[list[str], str]:
    """
    Parse a requirements.txt file and return (dep_names, parse_status).
    parse_status is "parsed" or "fallback" (empty / unreadable).
    """
    names = []
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                # Skip comments, blank lines, options, VCS deps
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                if _VCS_RE.match(line):
                    continue
                # Strip extras, markers, specifiers
                line = _EXTRA_RE.sub("", line)
                line = _MARKER_RE.sub("", line)
                line = _SPECIFIER_RE.sub("", line)
                name = line.strip()
                if name:
                    names.append(name)
    except OSError:
        return [], "fallback"
    return names, ("parsed" if names else "fallback")


# ── pyproject.toml parser ────────────────────────────────────────────────────

def _parse_pyproject_toml(path: str) -> tuple[list[str], str]:
    """
    Parse pyproject.toml and pull dependencies from:
      [project] dependencies = [...]
      [tool.poetry.dependencies] (exclude python itself)
    Returns (dep_names, parse_status).
    """
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            return [], "fallback"          # no TOML parser available

    try:
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
    except (OSError, Exception):
        return [], "fallback"

    names = []

    # PEP 621 format
    project_deps = data.get("project", {}).get("dependencies", [])
    for dep in project_deps:
        n = _specifier_strip(dep)
        if n:
            names.append(n)

    # Poetry format
    poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    for k in poetry_deps:
        if k.lower() != "python":
            n = _specifier_strip(k)
            if n:
                names.append(n)

    return names, ("parsed" if names else "fallback")


def _specifier_strip(raw: str) -> str:
    """Strip version spec from a dep string and return the bare name."""
    raw = _EXTRA_RE.sub("", raw)
    raw = _MARKER_RE.sub("", raw)
    raw = _SPECIFIER_RE.sub("", raw)
    return raw.strip()


# ── importability check ───────────────────────────────────────────────────────
# Map common package distribution names to their import names where they differ.
# Keep this minimal — only well-known mismatches that appear in real projects.
# Keys are always lowercase with hyphens (canonical pip form).
_IMPORT_NAME_MAP = {
    "pillow":            "PIL",
    "pyyaml":            "yaml",
    "scikit-learn":      "sklearn",
    "beautifulsoup4":    "bs4",
    "beautifulsoup":     "bs4",
    "opencv-python":     "cv2",
    "python-dateutil":   "dateutil",
    "python-dotenv":     "dotenv",
    "typing-extensions": "typing_extensions",
    "attrs":             "attr",
    "psycopg2-binary":   "psycopg2",
    "psycopg2-pool":     "psycopg2",
    "flask-wtf":         "flask_wtf",
    "flask-login":       "flask_login",
    "flask-sqlalchemy":  "flask_sqlalchemy",
    "flask-cors":        "flask_cors",
    "flask-migrate":     "flask_migrate",
}


def _to_import_name(dist_name: str) -> str:
    """Convert a distribution name to the likely importable module name."""
    # Normalise key: lowercase + hyphens (canonical form)
    key = dist_name.lower().replace("_", "-")
    if key in _IMPORT_NAME_MAP:
        return _IMPORT_NAME_MAP[key]
    # Default: lowercase, hyphens → underscores
    return dist_name.lower().replace("-", "_")


def _is_importable(import_name: str) -> bool:
    """Return True if import_name can be found by importlib without importing it."""
    spec = importlib.util.find_spec(import_name)
    return spec is not None


# ── main entry point ─────────────────────────────────────────────────────────

def cmd_env_check(repo_path: str) -> tuple[int, dict]:
    """
    Check whether declared dependencies of a repo are importable.

    Returns (exit_code, payload) where:
      exit_code = 0  if all deps importable (or no deps declared)
      exit_code = 1  if any deps are missing
      exit_code = 2  if no dependency file was found

    Payload fields:
      success               bool
      repo_path             str
      source_file           str | null
      parse_status          "parsed" | "fallback" | "not_found"
      dependency_count      int
      checked_dependencies  list[str]
      missing_dependencies  list[str]
      importable_dependencies list[str]
      summary               str
    """
    source_file = None
    dep_names: list[str] = []
    parse_status = "not_found"

    # ── discover dependency file ──────────────────────────────────────────────
    for candidate in _DEP_FILES:
        full_path = os.path.join(repo_path, candidate)
        if os.path.isfile(full_path):
            source_file = candidate
            if candidate.endswith(".toml"):
                dep_names, parse_status = _parse_pyproject_toml(full_path)
            else:
                dep_names, parse_status = _parse_requirements_txt(full_path)
            break

    if not source_file:
        result = {
            "success": False,
            "repo_path": repo_path,
            "source_file": None,
            "parse_status": "not_found",
            "dependency_count": 0,
            "checked_dependencies": [],
            "missing_dependencies": [],
            "importable_dependencies": [],
            "summary": "No dependency file found (tried: requirements.txt, pyproject.toml).",
        }
        print(json.dumps(result))
        return 2, result

    # ── check each dep ────────────────────────────────────────────────────────
    missing: list[str] = []
    importable: list[str] = []

    for dist_name in dep_names:
        import_name = _to_import_name(dist_name)
        if _is_importable(import_name):
            importable.append(dist_name)
        else:
            missing.append(dist_name)

    all_ok = len(missing) == 0
    exit_code = 0 if all_ok else 1

    if all_ok:
        summary = (
            f"All {len(dep_names)} declared dependencies are importable."
            if dep_names else
            "Dependency file found but no dependencies declared."
        )
    else:
        summary = (
            f"{len(missing)} of {len(dep_names)} declared dependencies are NOT importable: "
            f"{', '.join(missing)}."
        )

    result = {
        "success": all_ok,
        "repo_path": repo_path,
        "source_file": source_file,
        "parse_status": parse_status,
        "dependency_count": len(dep_names),
        "checked_dependencies": dep_names,
        "missing_dependencies": missing,
        "importable_dependencies": importable,
        "summary": summary,
    }
    print(json.dumps(result))
    return exit_code, result
