"""module_resolution_probe - Probe local Python module resolution candidates."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'module_resolution_probe', 'category': 'execution', 'description': 'Probe local Python module resolution candidates', 'handler': 'execution_probe', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'probe_mode': 'module_resolution'}


def run_module_resolution_probe(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_module_resolution_probe(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_module_resolution_probe(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
