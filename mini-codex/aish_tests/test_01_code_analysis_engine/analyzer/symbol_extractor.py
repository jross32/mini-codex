"""Symbol extraction from AST."""

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Optional


@dataclass
class Symbol:
    """Represents a code symbol (class, function, variable)."""
    name: str
    type: str  # "class", "function", "variable", "import"
    lineno: int
    col_offset: int
    docstring: Optional[str] = None
    params: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    references: Set[str] = field(default_factory=set)


class SymbolExtractor(ast.NodeVisitor):
    """Extract symbols from AST."""

    def __init__(self, filename: str = "<unknown>"):
        """Initialize extractor."""
        self.filename = filename
        self.symbols: Dict[str, Symbol] = {}
        self.current_scope: List[str] = []

    def extract(self, tree: ast.Module) -> Dict[str, Symbol]:
        """Extract all symbols from AST tree."""
        self.symbols.clear()
        self.current_scope.clear()
        self.visit(tree)
        return self.symbols

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        symbol = Symbol(
            name=node.name,
            type="class",
            lineno=node.lineno,
            col_offset=node.col_offset,
            docstring=ast.get_docstring(node),
            decorators=[d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list],
        )
        self.symbols[node.name] = symbol
        self.current_scope.append(node.name)
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        params = [arg.arg for arg in node.args.args]
        symbol = Symbol(
            name=node.name,
            type="function",
            lineno=node.lineno,
            col_offset=node.col_offset,
            docstring=ast.get_docstring(node),
            params=params,
            decorators=[d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list],
        )
        key = ".".join(self.current_scope + [node.name])
        self.symbols[key] = symbol
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statement."""
        for alias in node.names:
            symbol = Symbol(
                name=alias.asname or alias.name,
                type="import",
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
            self.symbols[f"import:{alias.name}"] = symbol
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from...import statement."""
        module = node.module or ""
        for alias in node.names:
            symbol = Symbol(
                name=alias.asname or alias.name,
                type="import",
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
            self.symbols[f"import:{module}.{alias.name}"] = symbol
        self.generic_visit(node)
