"""Simple inter-module coupling calculator."""

import ast
from pathlib import Path
from typing import Dict, Set


class CouplingAnalyzer:
    """Measure import-based coupling across Python files."""

    def __init__(self) -> None:
        self.imports_by_file: Dict[str, Set[str]] = {}

    def analyze_file(self, file_path: Path) -> Set[str]:
        """Extract imported top-level modules for a file."""
        with open(file_path, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=str(file_path))

        imports: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

        self.imports_by_file[str(file_path)] = imports
        return imports

    def analyze_directory(self, directory: Path) -> Dict[str, Set[str]]:
        """Analyze all Python files in a directory recursively."""
        result: Dict[str, Set[str]] = {}
        for file_path in directory.rglob("*.py"):
            if file_path.name.startswith("_"):
                continue
            result[str(file_path)] = self.analyze_file(file_path)
        return result

    def average_import_coupling(self) -> float:
        """Average number of imported modules per analyzed file."""
        if not self.imports_by_file:
            return 0.0
        total = sum(len(mods) for mods in self.imports_by_file.values())
        return total / len(self.imports_by_file)
