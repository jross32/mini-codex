"""change_risk_snapshot - Produce a lightweight composite repo risk snapshot."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'change_risk_snapshot', 'category': 'evaluation', 'description': 'Produce a lightweight composite repo risk snapshot', 'handler': 'change_risk_snapshot_plus', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_change_risk_snapshot(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_change_risk_snapshot(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_change_risk_snapshot(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
