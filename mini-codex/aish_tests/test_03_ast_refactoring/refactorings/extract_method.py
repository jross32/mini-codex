"""Extract-method style helper for repeated assignment patterns."""

import ast
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class ExtractionResult:
    """Result for a method extraction request."""

    extracted_name: str
    replacements: int
    helper_source: str


class ExtractMethodRefactoring:
    """Very small extract-method utility for repeated assignment expressions."""

    def find_repeated_assignments(self, source: str) -> List[Tuple[str, int]]:
        """Find repeated assignment expressions and occurrence count."""
        tree = ast.parse(source)
        counts = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.BinOp):
                expr = ast.unparse(node.value)
                counts[expr] = counts.get(expr, 0) + 1

        return sorted(
            [(expr, count) for expr, count in counts.items() if count > 1],
            key=lambda item: item[1],
            reverse=True,
        )

    def extract(self, source: str, method_name: str = "extracted_compute") -> ExtractionResult:
        """Extract repeated binop assignment expression into helper function source."""
        repeated = self.find_repeated_assignments(source)
        if not repeated:
            return ExtractionResult(method_name, 0, "")

        expr, count = repeated[0]
        helper = (
            f"def {method_name}(a, b):\n"
            f"    return {expr}\n"
        )
        return ExtractionResult(method_name, count, helper)
