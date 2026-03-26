"""reading_queue_planner - Recommend a reading order for understanding the repo."""

import json

from tools.generated_tool_support import run_catalog_tool


SPEC = {'name': 'reading_queue_planner', 'category': 'planning', 'description': 'Recommend a reading order for understanding the repo', 'handler': 'planner_by_patterns', 'args': [{'name': 'query', 'type': 'str', 'optional': True}, {'name': 'limit', 'type': 'int', 'optional': True, 'default': 50}], 'returns': 'success, tool, category, handler, matches, count, summary, elapsed_ms', 'patterns': ['README*', '*.md', '*.py']}


def run_reading_queue_planner(repo_path: str, query: str = None, limit: int = 50):
    return run_catalog_tool(repo_path, SPEC, query=query, limit=limit)


def cmd_reading_queue_planner(repo_path: str, query: str = None, limit: int = 50):
    code, payload = run_reading_queue_planner(repo_path, query=query, limit=limit)
    print(json.dumps(payload))
    return code, payload
