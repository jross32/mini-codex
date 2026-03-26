"""function_name_finder - Find Python function names."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'function_name_finder', 'category': 'discovery', 'description': 'Find Python function names', 'handler': 'python_symbol_finder', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'symbol_mode': 'functions'}


def run_function_name_finder(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_function_name_finder(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_function_name_finder(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
