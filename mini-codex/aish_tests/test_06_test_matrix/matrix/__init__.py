"""Test matrix builder and parameter expansion."""

from typing import Dict, List, Any, Generator, Tuple
from itertools import product
from dataclasses import dataclass


@dataclass
class TestCase:
    """Represents a generated test case."""
    id: str
    name: str
    parameters: Dict[str, Any]
    expected: Any = None
    tags: List[str] = None


class MatrixBuilder:
    """Build test matrices from parameter specifications."""

    def __init__(self):
        """Initialize builder."""
        self.parameters: Dict[str, List[Any]] = {}
        self.constraints: List[callable] = []
        self.test_count = 0

    def add_parameter(self, name: str, values: List[Any]) -> None:
        """Add parameter to matrix."""
        self.parameters[name] = values

    def add_constraint(self, constraint: callable) -> None:
        """Add constraint to filter parameter combinations."""
        self.constraints.append(constraint)

    def generate_matrix(self) -> Generator[TestCase, None, None]:
        """Generate all test cases from matrix."""
        param_names = list(self.parameters.keys())
        param_values = [self.parameters[name] for name in param_names]

        for combination in product(*param_values):
            params = dict(zip(param_names, combination))

            # Check constraints
            valid = all(constraint(params) for constraint in self.constraints)
            if not valid:
                continue

            self.test_count += 1
            test_id = f"test_{self.test_count:06d}"
            test_name = "_".join(f"{name}_{str(val)[:20]}" 
                                for name, val in params.items())

            yield TestCase(
                id=test_id,
                name=test_name,
                parameters=params,
            )

    def get_matrix_size(self) -> int:
        """Calculate total matrix size before constraints."""
        if not self.parameters:
            return 0
        size = 1
        for values in self.parameters.values():
            size *= len(values)
        return size

    def get_generated_count(self) -> int:
        """Get count of generated test cases."""
        return self.test_count
