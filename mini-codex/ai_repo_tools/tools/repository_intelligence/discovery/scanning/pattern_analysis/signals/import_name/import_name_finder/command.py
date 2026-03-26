"""import_name_finder - Find Python import names and where they appear."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'import_name_finder', 'category': 'discovery', 'description': 'Find Python import names and where they appear', 'handler': 'python_symbol_finder', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'symbol_mode': 'imports'}


def run_import_name_finder(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_import_name_finder(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_import_name_finder(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
