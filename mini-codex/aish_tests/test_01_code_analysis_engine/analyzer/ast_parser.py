"""AST parsing module for code analysis engine."""

import ast
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class ASTParser:
    """Parse Python source files into AST structures."""

    def __init__(self, timeout: float = 30.0):
        """Initialize parser with optional timeout."""
        self.timeout = timeout
        self.parse_count = 0
        self.error_count = 0

    def parse_file(self, filepath: Path) -> Optional[ast.Module]:
        """Parse a single Python file.
        
        Args:
            filepath: Path to Python file
            
        Returns:
            AST Module or None on error
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            return self.parse_source(source, str(filepath))
        except Exception as e:
            self.error_count += 1
            print(f"Error parsing {filepath}: {e}")
            return None

    def parse_source(self, source: str, filename: str = "<string>") -> Optional[ast.Module]:
        """Parse Python source code string.
        
        Args:
            source: Python source code
            filename: Optional filename for error reporting
            
        Returns:
            AST Module or None on error
        """
        try:
            tree = ast.parse(source, filename=filename)
            self.parse_count += 1
            return tree
        except SyntaxError as e:
            self.error_count += 1
            print(f"Syntax error in {filename} at line {e.lineno}: {e.msg}")
            return None
        except Exception as e:
            self.error_count += 1
            print(f"Parse error in {filename}: {e}")
            return None

    def parse_directory(self, dirpath: Path, recursive: bool = True) -> Dict[str, ast.Module]:
        """Parse all Python files in directory.
        
        Args:
            dirpath: Directory path
            recursive: Whether to search subdirectories
            
        Returns:
            Dict mapping file paths to AST modules
        """
        results = {}
        pattern = "**/*.py" if recursive else "*.py"
        
        for filepath in dirpath.glob(pattern):
            if filepath.name.startswith('_'):
                continue
            tree = self.parse_file(filepath)
            if tree:
                results[str(filepath)] = tree
        
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get parsing statistics."""
        return {
            "parsed_files": self.parse_count,
            "errors": self.error_count,
            "success_rate": self.parse_count / max(1, self.parse_count + self.error_count),
        }
