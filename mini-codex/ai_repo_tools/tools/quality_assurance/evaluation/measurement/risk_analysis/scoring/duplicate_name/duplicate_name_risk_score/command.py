"""duplicate_name_risk_score - Score ambiguity caused by duplicate file names."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'duplicate_name_risk_score', 'category': 'evaluation', 'description': 'Score ambiguity caused by duplicate file names', 'handler': 'score_duplicate_name_risk_plus', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_duplicate_name_risk_score(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_duplicate_name_risk_score(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_duplicate_name_risk_score(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
