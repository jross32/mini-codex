"""Template variable resolution."""

from typing import Dict, Any, List


class VariableResolver:
    """Resolve variables in templates."""

    def __init__(self, context: Dict[str, Any] = None):
        """Initialize resolver with context."""
        self.context = context or {}
        self.scopes: List[Dict[str, Any]] = [self.context]

    def resolve(self, variable_name: str) -> Any:
        """Resolve variable from nested path (e.g., 'user.name')."""
        parts = variable_name.split('.')
        value = None

        # Search through scopes from most recent
        for scope in reversed(self.scopes):
            if parts[0] in scope:
                value = scope[parts[0]]
                break

        if value is None:
            return f"${{{variable_name}}}"  # Return unresolved placeholder

        # Navigate nested path
        for part in parts[1:]:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = getattr(value, part, None)

            if value is None:
                return f"${{{variable_name}}}"

        return value

    def push_scope(self, scope: Dict[str, Any]) -> None:
        """Push new scope."""
        self.scopes.append(scope)

    def pop_scope(self) -> None:
        """Pop current scope."""
        if len(self.scopes) > 1:
            self.scopes.pop()

    def set_variable(self, name: str, value: Any) -> None:
        """Set variable in current scope."""
        self.scopes[-1][name] = value

    def get_undefined_vars(self, variables: List[str]) -> List[str]:
        """Find undefined variables."""
        undefined = []
        for var in variables:
            if self.resolve(var).startswith("${"):
                undefined.append(var)
        return undefined
