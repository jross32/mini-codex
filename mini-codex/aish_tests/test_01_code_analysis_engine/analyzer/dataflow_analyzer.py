"""Basic data flow analyzer for assignment/use tracking."""

import ast
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class VariableFlow:
    """Track definitions and uses for a variable."""

    name: str
    definitions: List[int] = field(default_factory=list)
    uses: List[int] = field(default_factory=list)


class DataflowAnalyzer(ast.NodeVisitor):
    """Analyze variable definitions and uses across functions."""

    def __init__(self) -> None:
        self.flows: Dict[str, VariableFlow] = {}
        self.current_scope: List[str] = []

    def analyze(self, tree: ast.AST) -> Dict[str, VariableFlow]:
        """Analyze AST and return variable flow map."""
        self.flows.clear()
        self.current_scope.clear()
        self.visit(tree)
        return self.flows

    def _key(self, name: str) -> str:
        if self.current_scope:
            return ".".join(self.current_scope + [name])
        return name

    def _get_or_create(self, key: str) -> VariableFlow:
        if key not in self.flows:
            self.flows[key] = VariableFlow(name=key)
        return self.flows[key]

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.current_scope.append(node.name)
        for arg in node.args.args:
            flow = self._get_or_create(self._key(arg.arg))
            flow.definitions.append(node.lineno)
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                flow = self._get_or_create(self._key(target.id))
                flow.definitions.append(node.lineno)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        key = self._key(node.id)
        flow = self._get_or_create(key)
        if isinstance(node.ctx, ast.Load):
            flow.uses.append(node.lineno)
        elif isinstance(node.ctx, ast.Store):
            flow.definitions.append(node.lineno)

    def get_uninitialized_reads(self) -> Set[str]:
        """Return names that appear as reads before any definition."""
        risky: Set[str] = set()
        for key, flow in self.flows.items():
            if flow.uses and not flow.definitions:
                risky.add(key)
        return risky
