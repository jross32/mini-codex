"""python_file_count_score - Score the repo based on Python file volume."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'python_file_count_score', 'category': 'evaluation', 'description': 'Score the repo based on Python file volume', 'handler': 'score_python_file_count', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_python_file_count_score(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_python_file_count_score(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_python_file_count_score(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
