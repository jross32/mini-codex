"""test_focus_planner - Recommend test files to inspect first."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'test_focus_planner', 'category': 'planning', 'description': 'Recommend test files to inspect first', 'handler': 'planner_by_patterns', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'patterns': ['test_*.py', '*_test.py', 'tests/*']}


def run_test_focus_planner(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_test_focus_planner(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_test_focus_planner(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
