"""import_complexity_score - Estimate import surface complexity."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'import_complexity_score', 'category': 'evaluation', 'description': 'Estimate import surface complexity', 'handler': 'score_import_complexity_plus', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_import_complexity_score(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_import_complexity_score(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_import_complexity_score(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
