"""python_syntax_sampler - Sample Python files and report syntax health."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'python_syntax_sampler', 'category': 'evaluation', 'description': 'Sample Python files and report syntax health', 'handler': 'python_syntax_sampler', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_python_syntax_sampler(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_python_syntax_sampler(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_python_syntax_sampler(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
