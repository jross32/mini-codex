"""shell_script_locator - Locate shell and PowerShell scripts."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'shell_script_locator', 'category': 'discovery', 'description': 'Locate shell and PowerShell scripts', 'handler': 'glob_locator', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'patterns': ['*.sh', '*.ps1', '*.bat', '*.cmd']}


def run_shell_script_locator(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_shell_script_locator(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_shell_script_locator(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
