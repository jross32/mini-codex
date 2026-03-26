"""imports_reader - Read Python import statements."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'imports_reader', 'category': 'reading', 'description': 'Read Python import statements', 'handler': 'structured_reader', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'read_mode': 'python_imports'}


def run_imports_reader(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_imports_reader(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_imports_reader(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
