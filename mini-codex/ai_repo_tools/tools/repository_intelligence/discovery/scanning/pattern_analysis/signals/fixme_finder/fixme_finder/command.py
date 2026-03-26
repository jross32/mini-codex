"""fixme_finder - Find FIXME markers in source files."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'fixme_finder', 'category': 'discovery', 'description': 'Find FIXME markers in source files', 'handler': 'text_search', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'terms': ['FIXME']}


def run_fixme_finder(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_fixme_finder(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_fixme_finder(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
