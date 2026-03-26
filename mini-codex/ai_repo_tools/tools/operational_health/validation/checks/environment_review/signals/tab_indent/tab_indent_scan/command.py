"""tab_indent_scan - Find files using hard tab indentation."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'tab_indent_scan', 'category': 'health', 'description': 'Find files using hard tab indentation', 'handler': 'health_scan', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'scan_mode': 'tab_indent'}


def run_tab_indent_scan(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_tab_indent_scan(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_tab_indent_scan(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
