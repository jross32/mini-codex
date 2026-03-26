"""text_excerpt_reader - Read plain text excerpts."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'text_excerpt_reader', 'category': 'reading', 'description': 'Read plain text excerpts', 'handler': 'structured_reader', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'read_mode': 'text'}


def run_text_excerpt_reader(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_text_excerpt_reader(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_text_excerpt_reader(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
