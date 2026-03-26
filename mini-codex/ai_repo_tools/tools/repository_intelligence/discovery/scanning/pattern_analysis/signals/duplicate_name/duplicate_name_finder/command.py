"""duplicate_name_finder - Find duplicate file names across directories."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'duplicate_name_finder', 'category': 'discovery', 'description': 'Find duplicate file names across directories', 'handler': 'duplicate_name_finder', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_duplicate_name_finder(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_duplicate_name_finder(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_duplicate_name_finder(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
