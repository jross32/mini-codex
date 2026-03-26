"""discovery_query_locator_001 - Locate files related to a query-driven discovery slice #1."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'discovery_query_locator_001', 'category': 'discovery', 'description': 'Locate files related to a query-driven discovery slice #1', 'handler': 'query_locator', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_discovery_query_locator_001(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_discovery_query_locator_001(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_discovery_query_locator_001(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
