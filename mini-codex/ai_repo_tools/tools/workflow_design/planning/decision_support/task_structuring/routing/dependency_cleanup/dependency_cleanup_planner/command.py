"""dependency_cleanup_planner - Recommend dependency-related files for cleanup review."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'dependency_cleanup_planner', 'category': 'planning', 'description': 'Recommend dependency-related files for cleanup review', 'handler': 'dependency_cleanup_planner', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'patterns': ['requirements*.txt', 'pyproject.toml', 'setup.py', 'package.json']}


def run_dependency_cleanup_planner(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_dependency_cleanup_planner(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_dependency_cleanup_planner(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
