"""notebook_parse_probe - Probe notebook parseability."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'notebook_parse_probe', 'category': 'execution', 'description': 'Probe notebook parseability', 'handler': 'execution_probe', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'probe_mode': 'notebook_parse'}


def run_notebook_parse_probe(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_notebook_parse_probe(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_notebook_parse_probe(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
