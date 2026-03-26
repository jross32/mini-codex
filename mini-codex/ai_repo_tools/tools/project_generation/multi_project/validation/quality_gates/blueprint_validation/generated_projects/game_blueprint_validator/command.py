"""
game_blueprint_validator - Validate game blueprint structure against README spec - reads README and verifies all declared system folders exist and contain code

Category: execution
Returns: success, blueprint_valid, folders_found, folders_valid, folders_missing, issues, summary, elapsed_ms

This is a Quality Control tool that validates game project structure matches declared architecture.
Works with ANY game sim (RPG, Cyberpunk, etc) - just reads the blueprint from README.
"""
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def _find_readme(repo_path: str) -> Optional[str]:
    """Find README.md or README.txt in repo."""
    repo = Path(repo_path)
    for readme_name in ["README.md", "README.txt", "readme.md", "readme.txt"]:
        readme_path = repo / readme_name
        if readme_path.exists():
            return str(readme_path)
    return None


def _extract_system_folders_from_readme(readme_content: str) -> List[str]:
    """Extract system folder names mentioned in README (look for patterns like 'core/', 'ui/', etc)."""
    # Look for common patterns: folder names in code blocks, lists, or mentioned as directories
    patterns = [
        r'(?:^|\n)\s*[-*]\s+(\w+)/\s*(?:folder|system|dir)?',  # - core/ folder
        r'(?:^|\n)\s*(?:folder|system|directory|dir)s?:\s*([a-z_/]+)',  # folders: core, ui, entities
        r'`([a-z_]+)/`',  # `core/`
        r'(?:system|folder|module|subsystem):\s*([a-z_]+)',  # system: core
        r'## ([A-Z][a-z]+)\s+(?:System|Folder)',  # ## Core System
    ]
    
    found_folders = set()
    
    for pattern in patterns:
        matches = re.finditer(pattern, readme_content, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            folder_name = match.group(1).lower().strip('/')
            # Filter out false positives (common words that aren't folder names)
            if folder_name and not folder_name in ['the', 'and', 'or', 'is', 'are', 'system', 'folder']:
                if len(folder_name) > 1 and not ' ' in folder_name:
                    found_folders.add(folder_name)
    
    return sorted(list(found_folders))


def _has_code_files(folder_path: Path) -> Tuple[bool, List[str]]:
    """Check if folder contains code files and return found file types."""
    if not folder_path.exists() or not folder_path.is_dir():
        return False, []
    
    code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.rb', '.go', '.rs'}
    found_files = []
    
    try:
        for item in folder_path.rglob('*'):
            if item.is_file() and item.suffix in code_extensions:
                found_files.append(item.suffix)
    except (PermissionError, OSError):
        pass
    
    return len(found_files) > 0, found_files


def run_game_blueprint_validator(repo_path: str, target_path: Optional[str] = None) -> Tuple[int, Dict]:
    """
    Validate game blueprint structure against README spec.
    
    This tool:
    1. Finds README.md/txt in the repo
    2. Extracts declared system folders (core, ui, entities, etc.)
    3. Checks each folder exists and contains code
    4. Returns validation report
    
    Works for ANY game type (RPG, Cyberpunk, etc) - structure-agnostic validation.

    Returns: success, blueprint_valid, folders_found, folders_valid, folders_missing, issues, summary, elapsed_ms
    """
    t0 = time.monotonic()
    
    issues: List[str] = []
    folders_found: List[str] = []
    folders_valid: List[str] = []
    folders_missing: List[str] = []
    
    project_root = Path(target_path) if target_path else Path(repo_path)

    # Step 1: Find README
    readme_path = _find_readme(str(project_root))
    if not readme_path:
        return 0, {
            "success": True,
            "blueprint_valid": False,
            "folders_found": [],
            "folders_valid": [],
            "folders_missing": [],
            "issues": ["No README.md found in repo - cannot extract blueprint"],
            "summary": "Blueprint validation failed: no README found",
            "elapsed_ms": round((time.monotonic() - t0) * 1000)
        }
    
    # Step 2: Read and parse README
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except Exception as e:
        return 0, {
            "success": True,
            "blueprint_valid": False,
            "folders_found": [],
            "folders_valid": [],
            "folders_missing": [],
            "issues": [f"Failed to read README: {str(e)}"],
            "summary": "Blueprint validation failed: could not read README",
            "elapsed_ms": round((time.monotonic() - t0) * 1000)
        }
    
    # Step 3: Extract system folders from README
    folders_found = _extract_system_folders_from_readme(readme_content)
    
    if not folders_found:
        return 0, {
            "success": True,
            "blueprint_valid": False,
            "folders_found": [],
            "folders_valid": [],
            "folders_missing": [],
            "issues": ["No system folders mentioned in README"],
            "summary": "Blueprint validation incomplete: no folder declarations found",
            "elapsed_ms": round((time.monotonic() - t0) * 1000)
        }
    
    # Step 4: Validate each folder exists and has code
    repo = project_root
    for folder_name in folders_found:
        folder_path = repo / folder_name
        
        if not folder_path.exists():
            folders_missing.append(folder_name)
            issues.append(f"Declared folder '{folder_name}' not found")
        else:
            has_code, file_types = _has_code_files(folder_path)
            if has_code:
                folders_valid.append(folder_name)
            else:
                folders_missing.append(folder_name)
                issues.append(f"Folder '{folder_name}' exists but contains no code files")
    
    # Determine overall validity
    blueprint_valid = len(folders_valid) == len(folders_found) and len(folders_missing) == 0
    
    payload = {
        "success": True,
        "project_root": str(project_root),
        "blueprint_valid": blueprint_valid,
        "folders_found": folders_found,
        "folders_valid": folders_valid,
        "folders_missing": folders_missing,
        "issues": issues,
        "summary": f"Blueprint validation: {len(folders_valid)}/{len(folders_found)} system folders have code" + 
                  (f"; Issues: {len(issues)}" if issues else ""),
        "elapsed_ms": round((time.monotonic() - t0) * 1000)
    }
    
    return 0, payload


def cmd_game_blueprint_validator(repo_path: str, target_path: Optional[str] = None):
    code, payload = run_game_blueprint_validator(repo_path, target_path=target_path)
    print(json.dumps(payload))
    return code, payload
