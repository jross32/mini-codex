"""test_density_score - Estimate how test-heavy the repo is."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'test_density_score', 'category': 'evaluation', 'description': 'Estimate how test-heavy the repo is', 'handler': 'score_test_density', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_test_density_score(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_test_density_score(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_test_density_score(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
