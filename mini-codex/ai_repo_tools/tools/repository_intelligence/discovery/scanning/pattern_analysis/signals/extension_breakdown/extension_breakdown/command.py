"""extension_breakdown - Count files by extension."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'extension_breakdown', 'category': 'discovery', 'description': 'Count files by extension', 'handler': 'extension_breakdown', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_extension_breakdown(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_extension_breakdown(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_extension_breakdown(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
