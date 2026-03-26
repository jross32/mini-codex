"""yaml_validity_sampler - Sample YAML files and report parse health."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'yaml_validity_sampler', 'category': 'evaluation', 'description': 'Sample YAML files and report parse health', 'handler': 'structured_validity_sampler', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'parse_mode': 'yaml'}


def run_yaml_validity_sampler(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_yaml_validity_sampler(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_yaml_validity_sampler(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
