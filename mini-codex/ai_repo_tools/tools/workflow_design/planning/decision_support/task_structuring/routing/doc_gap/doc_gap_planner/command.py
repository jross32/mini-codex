"""doc_gap_planner - Identify code-heavy areas with little nearby documentation."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'doc_gap_planner', 'category': 'planning', 'description': 'Identify code-heavy areas with little nearby documentation', 'handler': 'doc_gap_planner', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_doc_gap_planner(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_doc_gap_planner(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_doc_gap_planner(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
