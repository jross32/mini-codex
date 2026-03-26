"""Type annotation inference and addition."""

import ast
from typing import Dict, Optional, Any, List


class TypeAnnotator(ast.NodeTransformer):
    """Add type annotations to code."""

    def __init__(self):
        """Initialize annotator."""
        self.inferred_types: Dict[str, str] = {}
        self.annotation_count = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Add type hints to function."""
        # Infer return type from return statements
        return_type = self._infer_return_type(node)
        if return_type:
            node.returns = ast.Name(id=return_type, ctx=ast.Load())
            self.annotation_count += 1

        # Annotate parameters
        for arg in node.args.args:
            if not arg.annotation:
                inferred_type = self._infer_arg_type(arg.arg, node)
                if inferred_type:
                    arg.annotation = ast.Name(id=inferred_type, ctx=ast.Load())
                    self.annotation_count += 1

        self.generic_visit(node)
        return node

    def _infer_return_type(self, node: ast.FunctionDef) -> Optional[str]:
        """Infer return type from return statements."""
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value:
                if isinstance(child.value, ast.Constant):
                    if isinstance(child.value.value, bool):
                        return "bool"
                    elif isinstance(child.value.value, int):
                        return "int"
                    elif isinstance(child.value.value, str):
                        return "str"
                elif isinstance(child.value, ast.List):
                    return "List"
                elif isinstance(child.value, ast.Dict):
                    return "Dict"
        return None

    def _infer_arg_type(self, arg_name: str, func: ast.FunctionDef) -> Optional[str]:
        """Infer argument type from usage."""
        for node in ast.walk(func):
            if isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Name) and node.value.id == arg_name:
                    return "Sequence"
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == arg_name:
                    return "Callable"
        return None

    def get_annotation_count(self) -> int:
        """Get number of annotations added."""
        return self.annotation_count
