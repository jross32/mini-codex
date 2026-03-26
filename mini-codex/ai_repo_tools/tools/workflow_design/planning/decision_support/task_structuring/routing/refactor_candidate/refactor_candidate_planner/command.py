"""refactor_candidate_planner - Identify large files that are likely refactor candidates."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'refactor_candidate_planner', 'category': 'planning', 'description': 'Identify large files that are likely refactor candidates', 'handler': 'refactor_candidate_planner', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_refactor_candidate_planner(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_refactor_candidate_planner(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_refactor_candidate_planner(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
