"""evaluation_query_score_002 - Score risk for query-driven slice #2."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'evaluation_query_score_002', 'category': 'evaluation', 'description': 'Score risk for query-driven slice #2', 'handler': 'query_risk_score', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_evaluation_query_score_002(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_evaluation_query_score_002(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_evaluation_query_score_002(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
