"""empty_file_check - Find empty files."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'empty_file_check', 'category': 'health', 'description': 'Find empty files', 'handler': 'health_scan', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'scan_mode': 'empty_files'}


def run_empty_file_check(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_empty_file_check(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_empty_file_check(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
