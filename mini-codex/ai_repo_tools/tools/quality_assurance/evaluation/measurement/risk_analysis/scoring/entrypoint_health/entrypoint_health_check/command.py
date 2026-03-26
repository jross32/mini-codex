"""entrypoint_health_check - Check whether the repo exposes likely entrypoints."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'entrypoint_health_check', 'category': 'evaluation', 'description': 'Check whether the repo exposes likely entrypoints', 'handler': 'boolean_check', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'check_name': 'entrypoints_present'}


def run_entrypoint_health_check(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_entrypoint_health_check(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_entrypoint_health_check(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
