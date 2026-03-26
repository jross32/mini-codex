"""Template parsing and DSL interpretation."""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class TemplateNode:
    """Represents a template node."""
    type: str  # "text", "variable", "block", "conditional"
    value: str
    children: List["TemplateNode"] = None


class TemplateParser:
    """Parse template DSL."""

    def __init__(self):
        """Initialize parser."""
        self.patterns = {
            "variable": r"\{\{\s*(\w+(?:\.\w+)*)\s*\}\}",
            "block_start": r"\{%\s*(\w+)\s+(.+?)\s*%\}",
            "block_end": r"\{%\s*end\1\s*%\}",
            "conditional": r"\{%\s*if\s+(.+?)\s*%\}",
        }

    def parse(self, template: str) -> List[TemplateNode]:
        """Parse template string into AST."""
        nodes: List[TemplateNode] = []
        remaining = template
        
        while remaining:
            # Try to match variable
            var_match = re.search(self.patterns["variable"], remaining)
            cond_match = re.search(self.patterns["conditional"], remaining)

            if var_match and (not cond_match or var_match.start() < cond_match.start()):
                # Add text before variable
                if var_match.start() > 0:
                    nodes.append(TemplateNode("text", remaining[:var_match.start()]))
                
                # Add variable node
                var_name = var_match.group(1)
                nodes.append(TemplateNode("variable", var_name))
                remaining = remaining[var_match.end():]
            
            elif cond_match:
                # Add text before conditional
                if cond_match.start() > 0:
                    nodes.append(TemplateNode("text", remaining[:cond_match.start()]))
                
                # Parse conditional block
                condition = cond_match.group(1)
                block_end = remaining.find("{% endif %}")
                if block_end != -1:
                    block_content = remaining[cond_match.end():block_end]
                    child_nodes = self.parse(block_content)
                    nodes.append(TemplateNode(
                        "conditional", 
                        condition,
                        children=child_nodes
                    ))
                    remaining = remaining[block_end + 11:]
                else:
                    remaining = ""
            else:
                # No more patterns, add remaining text
                if remaining:
                    nodes.append(TemplateNode("text", remaining))
                break
        
        return nodes

    def get_variables(self, template: str) -> List[str]:
        """Extract all variables from template."""
        matches = re.findall(self.patterns["variable"], template)
        return list(set(matches))
