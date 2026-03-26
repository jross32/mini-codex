"""config_review_planner - Recommend configuration files for review."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'config_review_planner', 'category': 'planning', 'description': 'Recommend configuration files for review', 'handler': 'config_review_planner', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'patterns': ['*.json', '*.yml', '*.yaml', 'pyproject.toml', 'requirements*.txt', '.env*']}


def run_config_review_planner(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_config_review_planner(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_config_review_planner(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
