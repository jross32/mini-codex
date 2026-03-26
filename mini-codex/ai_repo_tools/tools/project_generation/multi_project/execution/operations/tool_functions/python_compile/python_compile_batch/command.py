"""python_compile_batch - Compile Python files to check syntax in batch."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'python_compile_batch', 'category': 'execution', 'description': 'Compile Python files to check syntax in batch', 'handler': 'execution_probe', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'probe_mode': 'python_compile'}


def run_python_compile_batch(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_python_compile_batch(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_python_compile_batch(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
