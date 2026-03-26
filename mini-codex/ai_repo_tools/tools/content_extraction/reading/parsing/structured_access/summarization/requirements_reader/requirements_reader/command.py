"""requirements_reader - Read Python requirements files."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'requirements_reader', 'category': 'reading', 'description': 'Read Python requirements files', 'handler': 'requirements_reader_plus', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'read_mode': 'requirements'}


def run_requirements_reader(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_requirements_reader(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_requirements_reader(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
