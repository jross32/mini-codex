"""json_parse_batch - Parse JSON files in batch."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'json_parse_batch', 'category': 'execution', 'description': 'Parse JSON files in batch', 'handler': 'execution_probe', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'probe_mode': 'json_parse'}


def run_json_parse_batch(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_json_parse_batch(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_json_parse_batch(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
