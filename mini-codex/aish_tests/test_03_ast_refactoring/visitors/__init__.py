"""AST Refactoring Tool - Visitors module."""

import ast
from typing import List, Dict, Any, Optional
from .rename_visitor import RenameVisitor

__all__ = ["VisitorBase", "RenameVisitor"]


class VisitorBase(ast.NodeTransformer):
    """Base class for AST visitors with transformation."""

    def __init__(self, filename: str = "<unknown>"):
        """Initialize visitor."""
        self.filename = filename
        self.changes: List[Dict[str, Any]] = []
        self.line_map: Dict[int, str] = {}

    def track_change(self, node: ast.AST, change_type: str, details: Dict) -> None:
        """Track a change made during transformation."""
        change = {
            "type": change_type,
            "line": getattr(node, 'lineno', None),
            "details": details,
        }
        self.changes.append(change)

    def get_changes(self) -> List[Dict[str, Any]]:
        """Get list of changes made."""
        return self.changes

    def reset(self) -> None:
        """Reset visitor state."""
        self.changes.clear()

    def validate_tree(self, tree: ast.Module) -> bool:
        """Validate AST tree integrity."""
        try:
            ast.fix_missing_locations(tree)
            compile(tree, self.filename, 'exec')
            return True
        except SyntaxError as e:
            print(f"Invalid tree after transformation: {e}")
            return False
