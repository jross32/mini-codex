"""docstring_coverage_estimator - Estimate Python docstring coverage."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'docstring_coverage_estimator', 'category': 'evaluation', 'description': 'Estimate Python docstring coverage', 'handler': 'score_docstring_coverage', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_docstring_coverage_estimator(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_docstring_coverage_estimator(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_docstring_coverage_estimator(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
