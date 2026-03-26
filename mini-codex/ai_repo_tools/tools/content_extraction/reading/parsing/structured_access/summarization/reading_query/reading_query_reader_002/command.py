"""reading_query_reader_002 - Read focused excerpts for query-driven slice #2."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'reading_query_reader_002', 'category': 'reading', 'description': 'Read focused excerpts for query-driven slice #2', 'handler': 'query_excerpt_reader', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_reading_query_reader_002(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_reading_query_reader_002(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_reading_query_reader_002(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
