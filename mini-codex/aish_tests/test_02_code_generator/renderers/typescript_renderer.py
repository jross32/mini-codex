"""Render simple TypeScript code artifacts."""

from typing import Dict, List


class TypeScriptRenderer:
    """Render basic TypeScript functions and interfaces."""

    def render_function(self, name: str, params: List[str], return_type: str = "void") -> str:
        """Render a TypeScript function signature and empty body."""
        typed_params = ", ".join(f"{param}: any" for param in params)
        return (
            f"function {name}({typed_params}): {return_type} {{\n"
            "  // TODO: implement\n"
            "}\n"
        )

    def render_interface(self, name: str, fields: Dict[str, str]) -> str:
        """Render a TypeScript interface."""
        lines = [f"interface {name} {{"]
        for field_name, field_type in fields.items():
            lines.append(f"  {field_name}: {field_type};")
        lines.append("}")
        return "\n".join(lines) + "\n"
