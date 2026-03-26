"""json_summary_reader - Summarize JSON files."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'json_summary_reader', 'category': 'reading', 'description': 'Summarize JSON files', 'handler': 'json_summary_reader_plus', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'read_mode': 'json'}


def run_json_summary_reader(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_json_summary_reader(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_json_summary_reader(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
