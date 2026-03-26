"""API endpoint extraction from code."""

import ast
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Endpoint:
    """Represents an API endpoint."""
    name: str
    method: str  # GET, POST, etc.
    path: str
    params: Dict[str, str] = None
    request_body: Dict[str, Any] = None
    response: Dict[str, Any] = None
    docstring: Optional[str] = None


class EndpointExtractor(ast.NodeVisitor):
    """Extract API endpoints from code."""

    def __init__(self):
        """Initialize extractor."""
        self.endpoints: List[Endpoint] = []
        self.current_class: Optional[str] = None

    def extract(self, tree: ast.Module) -> List[Endpoint]:
        """Extract endpoints from AST."""
        self.endpoints = []
        self.visit(tree)
        return self.endpoints

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function and check for endpoint markers."""
        # Look for decorator that indicates endpoint
        for decorator in node.decorator_list:
            if self._is_endpoint_decorator(decorator):
                endpoint = self._extract_endpoint(node, decorator)
                if endpoint:
                    self.endpoints.append(endpoint)

        self.generic_visit(node)

    def _is_endpoint_decorator(self, decorator: ast.AST) -> bool:
        """Check if decorator marks an endpoint."""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr in ["get", "post", "put", "delete"]
            elif isinstance(decorator.func, ast.Name):
                return decorator.func.id in ["get", "post", "put", "delete"]
        return False

    def _extract_endpoint(self, func: ast.FunctionDef, decorator: ast.AST) -> Optional[Endpoint]:
        """Extract endpoint information from function."""
        try:
            method = "GET"
            path = "/api"

            if isinstance(decorator, ast.Call):
                if decorator.args:
                    if isinstance(decorator.args[0], ast.Constant):
                        path = decorator.args[0].value
                if isinstance(decorator.func, ast.Attribute):
                    method = decorator.func.attr.upper()

            return Endpoint(
                name=func.name,
                method=method,
                path=path,
                docstring=ast.get_docstring(func),
            )
        except Exception:
            return None

    def get_endpoints_by_method(self, method: str) -> List[Endpoint]:
        """Get endpoints filtered by HTTP method."""
        return [ep for ep in self.endpoints if ep.method == method]
