"""notebook_cell_counter - Count notebook cells in .ipynb files."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'notebook_cell_counter', 'category': 'reading', 'description': 'Count notebook cells in .ipynb files', 'handler': 'structured_reader', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'read_mode': 'notebook'}


def run_notebook_cell_counter(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_notebook_cell_counter(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_notebook_cell_counter(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
