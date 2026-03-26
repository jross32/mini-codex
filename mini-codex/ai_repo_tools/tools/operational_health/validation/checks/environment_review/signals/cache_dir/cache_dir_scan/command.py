"""cache_dir_scan - Find cache directories."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'cache_dir_scan', 'category': 'health', 'description': 'Find cache directories', 'handler': 'health_scan', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'scan_mode': 'cache_dirs'}


def run_cache_dir_scan(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_cache_dir_scan(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_cache_dir_scan(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
