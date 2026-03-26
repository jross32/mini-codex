"""Dependency resolution and cycle detection."""

from typing import Dict, List, Set, Tuple
from dataclasses import dataclass


@dataclass
class Dependency:
    """Represents a dependency relationship."""
    source: str
    target: str
    type: str = "uses"  # "uses", "imports", "extends", "calls"
    count: int = 1


class DependencyResolver:
    """Build and analyze dependency graphs."""

    def __init__(self):
        """Initialize resolver."""
        self.dependencies: Dict[str, Set[str]] = {}
        self.reverse_deps: Dict[str, Set[str]] = {}
        self.cycles: List[List[str]] = []

    def add_dependency(self, source: str, target: str) -> None:
        """Add dependency edge."""
        if source not in self.dependencies:
            self.dependencies[source] = set()
        self.dependencies[source].add(target)

        if target not in self.reverse_deps:
            self.reverse_deps[target] = set()
        self.reverse_deps[target].add(source)

    def find_cycles(self) -> List[List[str]]:
        """Find all circular dependencies using DFS."""
        self.cycles = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.dependencies.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path[:])
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in self.cycles:
                        self.cycles.append(cycle)

            rec_stack.discard(node)

        for node in self.dependencies:
            if node not in visited:
                dfs(node, [])

        return self.cycles

    def get_dependents(self, symbol: str) -> Set[str]:
        """Get all symbols that depend on this symbol."""
        return self.reverse_deps.get(symbol, set())

    def get_dependencies(self, symbol: str) -> Set[str]:
        """Get all dependencies of this symbol."""
        return self.dependencies.get(symbol, set())

    def calculate_depth(self, symbol: str) -> int:
        """Calculate dependency tree depth."""
        if symbol not in self.dependencies or not self.dependencies[symbol]:
            return 0

        max_depth = 0
        for dep in self.dependencies[symbol]:
            max_depth = max(max_depth, 1 + self.calculate_depth(dep))

        return max_depth

    def get_stats(self) -> Dict[str, any]:
        """Get dependency statistics."""
        total_deps = sum(len(deps) for deps in self.dependencies.values())
        return {
            "total_symbols": len(self.dependencies),
            "total_dependencies": total_deps,
            "cycles_found": len(self.cycles),
            "avg_deps_per_symbol": total_deps / max(1, len(self.dependencies)),
        }
