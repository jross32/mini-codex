"""health_query_scan_001 - Scan health issues for query-driven slice #1."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'health_query_scan_001', 'category': 'health', 'description': 'Scan health issues for query-driven slice #1', 'handler': 'query_health_scan', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_health_query_scan_001(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_health_query_scan_001(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_health_query_scan_001(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
