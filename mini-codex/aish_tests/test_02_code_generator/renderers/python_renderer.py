"""Render simple Python code artifacts."""

from typing import Dict, List


class PythonRenderer:
    """Render basic Python class and function snippets."""

    def render_function(self, name: str, params: List[str], body: str) -> str:
        """Render a Python function definition."""
        args = ", ".join(params)
        body_line = body if body.strip() else "pass"
        return f"def {name}({args}):\n    {body_line}\n"

    def render_class(self, name: str, methods: Dict[str, str]) -> str:
        """Render a class where values map to method body lines."""
        lines = [f"class {name}:"]
        if not methods:
            lines.append("    pass")
            return "\n".join(lines) + "\n"

        for method_name, body in methods.items():
            lines.append(f"    def {method_name}(self):")
            lines.append(f"        {body if body.strip() else 'pass'}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"
