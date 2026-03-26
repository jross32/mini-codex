import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_PROMPT = "restaurant website with online ordering"
PROJECT_REL = "aish_tests/ai_app_generator"
PIPELINE_REL = f"{PROJECT_REL}/.ai_app_pipeline"


def repo_root(repo_path: str) -> Path:
    return Path(repo_path).resolve()


def project_dir(repo_path: str) -> Path:
    p = repo_root(repo_path) / PROJECT_REL
    p.mkdir(parents=True, exist_ok=True)
    return p


def pipeline_dir(repo_path: str) -> Path:
    p = repo_root(repo_path) / PIPELINE_REL
    p.mkdir(parents=True, exist_ok=True)
    return p


def project_root(repo_path: str) -> Path:
    return project_dir(repo_path)


def ensure_project_dirs(repo_path: str) -> None:
    root = project_root(repo_path)
    (root / "backend").mkdir(parents=True, exist_ok=True)
    (root / "frontend").mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}
