"""yaml_summary_reader - Summarize YAML files."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'yaml_summary_reader', 'category': 'reading', 'description': 'Summarize YAML files', 'handler': 'structured_reader', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'read_mode': 'yaml'}


def run_yaml_summary_reader(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_yaml_summary_reader(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_yaml_summary_reader(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
