"""auth_review_planner - Find authentication and authorization related files."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'auth_review_planner', 'category': 'planning', 'description': 'Find authentication and authorization related files', 'handler': 'auth_review_planner', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'needles': ['auth', 'login', 'permission', 'session', 'token']}


def run_auth_review_planner(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_auth_review_planner(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_auth_review_planner(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
