"""test_presence_check - Check whether the repo includes tests."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'test_presence_check', 'category': 'evaluation', 'description': 'Check whether the repo includes tests', 'handler': 'boolean_check', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'check_name': 'tests_present'}


def run_test_presence_check(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_test_presence_check(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_test_presence_check(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
