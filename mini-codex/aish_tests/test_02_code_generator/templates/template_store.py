"""Template storage and retrieval."""

from pathlib import Path
from typing import Dict, Optional


class TemplateStore:
    """Manage template storage and loading."""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize store."""
        self.template_dir = template_dir
        self.cache: Dict[str, str] = {}

    def load_template(self, name: str) -> str:
        """Load template by name."""
        if name in self.cache:
            return self.cache[name]

        if self.template_dir:
            template_path = self.template_dir / f"{name}.template"
            if template_path.exists():
                with open(template_path, 'r') as f:
                    content = f.read()
                self.cache[name] = content
                return content

        raise ValueError(f"Template not found: {name}")

    def store_template(self, name: str, content: str) -> None:
        """Store template."""
        self.cache[name] = content

    def list_templates(self) -> list:
        """List available templates."""
        return list(self.cache.keys())

    def clear_cache(self) -> None:
        """Clear template cache."""
        self.cache.clear()
