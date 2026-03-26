"""script_entrypoint_probe - Probe for Python script entrypoints."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'script_entrypoint_probe', 'category': 'execution', 'description': 'Probe for Python script entrypoints', 'handler': 'execution_probe', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'probe_mode': 'script_entrypoints'}


def run_script_entrypoint_probe(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_script_entrypoint_probe(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_script_entrypoint_probe(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
