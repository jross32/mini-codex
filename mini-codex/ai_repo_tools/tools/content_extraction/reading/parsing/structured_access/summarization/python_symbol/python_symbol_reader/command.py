"""python_symbol_reader - Summarize Python imports, classes, and functions."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'python_symbol_reader', 'category': 'reading', 'description': 'Summarize Python imports, classes, and functions', 'handler': 'structured_reader', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'read_mode': 'python_symbols'}


def run_python_symbol_reader(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_python_symbol_reader(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_python_symbol_reader(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
