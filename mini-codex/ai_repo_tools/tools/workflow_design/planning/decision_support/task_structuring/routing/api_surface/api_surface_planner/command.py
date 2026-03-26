"""api_surface_planner - Find route, endpoint, and handler files."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'api_surface_planner', 'category': 'planning', 'description': 'Find route, endpoint, and handler files', 'handler': 'api_surface_planner', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'needles': ['api', 'route', 'endpoint', 'handler', 'controller']}


def run_api_surface_planner(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_api_surface_planner(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_api_surface_planner(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
