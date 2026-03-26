"""Build dependency graph structure."""

from typing import Dict, Set, List, Tuple
from collections import defaultdict, deque


class BuildGraph:
    """Represents task dependency graph."""

    def __init__(self):
        """Initialize graph."""
        self.tasks: Dict[str, Any] = {}
        self.edges: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_edges: Dict[str, Set[str]] = defaultdict(set)

    def add_task(self, task) -> None:
        """Add task to graph."""
        self.tasks[task.name] = task

        # Add edges for dependencies
        for dep in task.dependencies:
            self.edges[dep].add(task.name)
            self.reverse_edges[task.name].add(dep)

    def get_ready_tasks(self, completed: Set[str]) -> List[str]:
        """Get tasks ready to execute."""
        ready = []
        for task_name, task in self.tasks.items():
            if task_name not in completed:
                deps_met = all(dep in completed for dep in self.reverse_edges[task_name])
                if deps_met:
                    ready.append(task_name)
        return ready

    def find_cycles(self) -> List[List[str]]:
        """Detect circular dependencies."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        cycles: List[List[str]] = []

        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path_copy = path + [node]

            for neighbor in self.edges.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path_copy)
                elif neighbor in rec_stack:
                    cycle = path_copy[path_copy.index(neighbor):] + [neighbor]
                    cycles.append(cycle)

            rec_stack.discard(node)

        for task in self.tasks:
            if task not in visited:
                dfs(task, [])

        return cycles

    def get_critical_path(self) -> List[str]:
        """Get longest path through graph."""
        distances: Dict[str, float] = {task: 0.0 for task in self.tasks}

        # Topological sort + longest path
        sorted_tasks = self._topological_sort()
        for task_name in sorted_tasks:
            for dependent in self.edges.get(task_name, set()):
                task = self.tasks[task_name]
                distance = distances[task_name] + task.get_duration()
                distances[dependent] = max(distances[dependent], distance)

        return sorted_tasks

    def _topological_sort(self) -> List[str]:
        """Topological sort of tasks."""
        in_degree = {task: len(deps) for task, deps in self.reverse_edges.items()}
        queue = deque([task for task, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            task = queue.popleft()
            result.append(task)
            for dependent in self.edges.get(task, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        return result
