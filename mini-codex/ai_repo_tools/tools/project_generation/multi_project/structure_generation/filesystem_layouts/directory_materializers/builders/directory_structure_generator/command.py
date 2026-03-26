"""
directory_structure_generator - Create nested directory structures from JSON spec

Category: execution
Returns: success, dirs_created, files_created, summary, elapsed_ms

NOTE: This tool was scaffolded by toolmaker. Implements nested dir creation from JSON.
"""
import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple


def run_directory_structure_generator(repo_path: str, spec_json: Optional[str] = None) -> Tuple[int, Dict]:
    """
    Create nested directory structures from JSON spec.
    
    spec_json is a JSON string with structure like:
    {
      "base": "aish_tests",
      "dirs": ["game", "game/core", "game/ui", "game/data"],
      "files": {
        "game/__init__.py": "",
        "game/main.py": "# Game entry point"
      }
    }
    
    Returns: success, dirs_created, files_created, summary, elapsed_ms
    """
    t0 = time.monotonic()
    
    dirs_created = []
    files_created = []
    errors = []
    
    if not spec_json:
        return 2, {
            "success": False,
            "dirs_created": [],
            "files_created": [],
            "errors": ["spec_json is required"],
            "summary": "No spec provided",
            "elapsed_ms": 0
        }
    
    try:
        spec = json.loads(spec_json)
    except json.JSONDecodeError as e:
        return 2, {
            "success": False,
            "dirs_created": [],
            "files_created": [],
            "errors": [f"Invalid JSON: {str(e)}"],
            "summary": "JSON parse error",
            "elapsed_ms": 0
        }
    
    base_dir = spec.get("base", "aish_tests")
    dirs_to_create = spec.get("dirs", [])
    files_to_create = spec.get("files", {})
    
    repo_path_obj = Path(repo_path)
    base_path = repo_path_obj / base_dir
    
    # Create directories
    for dir_path in dirs_to_create:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            dirs_created.append(str(dir_path))
        except OSError as e:
            errors.append(f"Failed to create dir {dir_path}: {str(e)}")
    
    # Create files
    for file_path_str, content in files_to_create.items():
        full_path = base_path / file_path_str
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            files_created.append(str(file_path_str))
        except OSError as e:
            errors.append(f"Failed to create file {file_path_str}: {str(e)}")
    
    success = len(errors) == 0
    payload = {
        "success": success,
        "dirs_created": dirs_created,
        "files_created": files_created,
        "errors": errors,
        "summary": f"Created {len(dirs_created)} directories and {len(files_created)} files in {base_dir}",
        "elapsed_ms": round((time.monotonic() - t0) * 1000)
    }
    
    return 0 if success else 1, payload


def cmd_directory_structure_generator(repo_path: str, spec_json: Optional[str] = None):
    code, payload = run_directory_structure_generator(repo_path, spec_json=spec_json)
    print(json.dumps(payload))
    return code, payload
