"""Code metrics calculation."""

import ast
from typing import Dict, Any, Optional


class MetricsCalculator(ast.NodeVisitor):
    """Calculate code metrics from AST."""

    def __init__(self):
        """Initialize metrics calculator."""
        self.cyclomatic_complexity = 0
        self.function_count = 0
        self.class_count = 0
        self.line_count = 0
        self.nesting_depth = 0
        self.max_nesting = 0

    def calculate(self, tree: ast.Module) -> Dict[str, Any]:
        """Calculate metrics for AST tree."""
        self.cyclomatic_complexity = 1
        self.function_count = 0
        self.class_count = 0
        self.nesting_depth = 0
        self.max_nesting = 0

        if tree.body:
            self.line_count = max(node.lineno for node in ast.walk(tree) 
                                  if hasattr(node, 'lineno'))
        
        self.visit(tree)

        return {
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "functions": self.function_count,
            "classes": self.class_count,
            "complexity_per_function": (
                self.cyclomatic_complexity / max(1, self.function_count)
            ),
            "max_nesting_depth": self.max_nesting,
            "lines_of_code": self.line_count,
        }

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function and track complexity."""
        self.function_count += 1
        self.nesting_depth += 1
        self.max_nesting = max(self.max_nesting, self.nesting_depth)
        self.generic_visit(node)
        self.nesting_depth -= 1

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class."""
        self.class_count += 1
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        """Track if statements (add to complexity)."""
        self.cyclomatic_complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Track for loops."""
        self.cyclomatic_complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        """Track while loops."""
        self.cyclomatic_complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Track except handlers."""
        self.cyclomatic_complexity += 1
        self.generic_visit(node)
