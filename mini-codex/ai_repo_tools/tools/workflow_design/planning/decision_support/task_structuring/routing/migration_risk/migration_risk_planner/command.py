"""migration_risk_planner - Find migration and schema evolution files."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'migration_risk_planner', 'category': 'planning', 'description': 'Find migration and schema evolution files', 'handler': 'migration_risk_planner', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'needles': ['migration', 'migrate', 'alembic', 'schema']}


def run_migration_risk_planner(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_migration_risk_planner(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_migration_risk_planner(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
