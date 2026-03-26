"""execution_query_probe_001 - Probe parse and entrypoint signals for query-driven slice #1."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'execution_query_probe_001', 'category': 'execution', 'description': 'Probe parse and entrypoint signals for query-driven slice #1', 'handler': 'query_parse_probe', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_execution_query_probe_001(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_execution_query_probe_001(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_execution_query_probe_001(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
