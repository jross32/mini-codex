"""planning_query_planner_001 - Plan review targets for query-driven slice #1."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'planning_query_planner_001', 'category': 'planning', 'description': 'Plan review targets for query-driven slice #1', 'handler': 'query_planner', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_planning_query_planner_001(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_planning_query_planner_001(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_planning_query_planner_001(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
