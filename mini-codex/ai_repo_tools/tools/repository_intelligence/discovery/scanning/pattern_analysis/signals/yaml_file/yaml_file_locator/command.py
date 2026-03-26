"""yaml_file_locator - Locate YAML files in the repo."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'yaml_file_locator', 'category': 'discovery', 'description': 'Locate YAML files in the repo', 'handler': 'glob_locator', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'patterns': ['*.yml', '*.yaml']}


def run_yaml_file_locator(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_yaml_file_locator(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_yaml_file_locator(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
