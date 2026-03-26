"""large_file_finder - Find the largest files in the repo."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'large_file_finder', 'category': 'discovery', 'description': 'Find the largest files in the repo', 'handler': 'large_file_finder', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_large_file_finder(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_large_file_finder(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_large_file_finder(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
