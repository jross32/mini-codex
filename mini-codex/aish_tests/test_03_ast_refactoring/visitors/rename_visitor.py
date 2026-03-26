"""AST Renaming visitor for symbol renaming refactoring."""

import ast
from typing import Dict, Set


class RenameVisitor(ast.NodeTransformer):
    """Rename symbols throughout AST."""

    def __init__(self, old_name: str, new_name: str):
        """Initialize renaming visitor."""
        self.old_name = old_name
        self.new_name = new_name
        self.rename_count = 0
        self.scope_stack: list = [set()]

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Visit function definition."""
        if node.name == self.old_name:
            node.name = self.new_name
            self.rename_count += 1

        # Track new scope
        self.scope_stack.append(set(arg.arg for arg in node.args.args))
        self.generic_visit(node)
        self.scope_stack.pop()

        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Visit class definition."""
        if node.name == self.old_name:
            node.name = self.new_name
            self.rename_count += 1

        self.scope_stack.append(set())
        self.generic_visit(node)
        self.scope_stack.pop()

        return node

    def visit_Name(self, node: ast.Name) -> ast.Name:
        """Visit name reference."""
        if node.id == self.old_name:
            # Check scope - don't rename if it's in local scope
            is_local = any(self.old_name in scope for scope in self.scope_stack)
            if not is_local:
                node.id = self.new_name
                self.rename_count += 1

        return node

    def visit_arg(self, node: ast.arg) -> ast.arg:
        """Visit function argument."""
        if node.arg == self.old_name:
            node.arg = self.new_name
            self.rename_count += 1
        return node

    def get_rename_count(self) -> int:
        """Get number of renames performed."""
        return self.rename_count
