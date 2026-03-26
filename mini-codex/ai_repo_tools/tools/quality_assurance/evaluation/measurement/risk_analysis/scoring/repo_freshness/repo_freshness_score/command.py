"""repo_freshness_score - Estimate freshness from recent file changes."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'repo_freshness_score', 'category': 'evaluation', 'description': 'Estimate freshness from recent file changes', 'handler': 'score_repo_freshness', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_repo_freshness_score(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_repo_freshness_score(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_repo_freshness_score(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
