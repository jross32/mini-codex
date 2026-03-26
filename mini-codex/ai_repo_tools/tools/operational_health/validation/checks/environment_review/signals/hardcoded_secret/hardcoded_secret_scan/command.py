"""hardcoded_secret_scan - Find likely hardcoded secrets."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'hardcoded_secret_scan', 'category': 'health', 'description': 'Find likely hardcoded secrets', 'handler': 'health_scan', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'scan_mode': 'hardcoded_secrets'}


def run_hardcoded_secret_scan(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_hardcoded_secret_scan(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_hardcoded_secret_scan(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
