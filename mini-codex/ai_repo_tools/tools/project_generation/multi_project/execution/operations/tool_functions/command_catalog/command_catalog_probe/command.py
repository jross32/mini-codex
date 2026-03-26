"""command_catalog_probe - Probe the registered tool catalog."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'command_catalog_probe', 'category': 'execution', 'description': 'Probe the registered tool catalog', 'handler': 'execution_probe', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'probe_mode': 'command_catalog'}


def run_command_catalog_probe(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_command_catalog_probe(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_command_catalog_probe(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
