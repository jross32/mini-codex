"""logging_improvement_planner - Find files that likely need logging cleanup."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'logging_improvement_planner', 'category': 'planning', 'description': 'Find files that likely need logging cleanup', 'handler': 'logging_improvement_planner', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'terms': ['print(', 'logging.', 'logger.']}


def run_logging_improvement_planner(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_logging_improvement_planner(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_logging_improvement_planner(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
