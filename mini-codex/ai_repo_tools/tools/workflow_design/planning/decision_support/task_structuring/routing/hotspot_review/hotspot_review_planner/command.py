"""hotspot_review_planner - Combine size and recency to find review hotspots."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'hotspot_review_planner', 'category': 'planning', 'description': 'Combine size and recency to find review hotspots', 'handler': 'hotspot_review_planner_plus', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms'}


def run_hotspot_review_planner(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_hotspot_review_planner(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_hotspot_review_planner(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
