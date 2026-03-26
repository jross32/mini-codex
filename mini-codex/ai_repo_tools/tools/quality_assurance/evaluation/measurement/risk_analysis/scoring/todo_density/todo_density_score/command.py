"""todo_density_score - Estimate TODO density across source files."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'todo_density_score', 'category': 'evaluation', 'description': 'Estimate TODO density across source files', 'handler': 'score_todo_density', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_todo_density_score(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_todo_density_score(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_todo_density_score(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
