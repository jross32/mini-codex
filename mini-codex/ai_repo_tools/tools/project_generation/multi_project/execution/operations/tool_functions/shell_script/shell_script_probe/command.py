"""shell_script_probe - Probe shell scripts for presence and size."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'shell_script_probe', 'category': 'execution', 'description': 'Probe shell scripts for presence and size', 'handler': 'execution_probe', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'probe_mode': 'shell_scripts'}


def run_shell_script_probe(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_shell_script_probe(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_shell_script_probe(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
