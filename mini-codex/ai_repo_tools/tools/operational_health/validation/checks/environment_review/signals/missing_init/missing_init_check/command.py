"""missing_init_check - Find Python packages missing __init__.py."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'missing_init_check', 'category': 'health', 'description': 'Find Python packages missing __init__.py', 'handler': 'health_scan', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'scan_mode': 'missing_init'}


def run_missing_init_check(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_missing_init_check(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_missing_init_check(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
