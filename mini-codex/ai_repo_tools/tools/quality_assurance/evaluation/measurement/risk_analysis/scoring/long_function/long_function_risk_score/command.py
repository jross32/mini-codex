"""long_function_risk_score - Estimate risk from long Python functions."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'long_function_risk_score', 'category': 'evaluation', 'description': 'Estimate risk from long Python functions', 'handler': 'score_long_function_risk_plus', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_long_function_risk_score(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_long_function_risk_score(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_long_function_risk_score(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
