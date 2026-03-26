#!/usr/bin/env python3
"""
symbol_graph v0 - Isolated prototype (no integration)

Input: repo path
Process: scan Python files, parse with stdlib ast
Output: JSON with symbols and edges
"""

import ast
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Set, Any


class SymbolGraphParser:
    """Minimal symbol graph AST parser."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.symbols: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, str]] = []
        self.python_files: List[Path] = []
        self.parse_time_ms = 0
        
    def collect_python_files(self) -> None:
        """Find all Python files in repo, excluding common ignored dirs."""
        ignored_dirs = {'.venv', 'venv', '__pycache__', '.git', 'node_modules', 
                       '.egg-info', 'dist', 'build', '.tox', 'alembic'}
        
        for root, dirs, files in os.walk(self.repo_path):
            # Filter dirs in-place to skip ignored ones
            dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith('.')]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    self.python_files.append(Path(root) / file)
    
    def extract_imports(self, tree: ast.AST, file_path: str) -> Set[str]:
        """Extract top-level imports from AST."""
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])  # Get top-level module
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])  # Get top-level module
        return imports
    
    def extract_exports(self, tree: ast.AST) -> Set[str]:
        """Extract top-level class and function definitions."""
        exports = set()
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                exports.add(node.name)
        return exports
    
    def extract_internal_calls(self, tree: ast.AST) -> List[Dict[str, str]]:
        """Extract function/method calls within the file (simplified)."""
        calls = []
        call_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    call_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    # For method calls, track just the method name
                    call_names.add(node.func.attr)
        
        # Return first few unique calls (keep it deterministic and minimal)
        for call_name in sorted(list(call_names))[:5]:
            calls.append({"from": "module", "to": call_name})
        return calls
    
    def parse_file(self, file_path: Path) -> None:
        """Parse a single Python file and extract symbols."""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            # Relative path from repo root
            rel_path = file_path.relative_to(self.repo_path).as_posix()
            
            imports = self.extract_imports(tree, rel_path)
            exports = self.extract_exports(tree)
            internal_calls = self.extract_internal_calls(tree)
            
            self.symbols[rel_path] = {
                "imports": sorted(list(imports)),
                "exports": sorted(list(exports)),
                "internal_calls": internal_calls
            }
                        
        except (SyntaxError, UnicodeDecodeError, Exception) as e:
            # Skip files that can't be parsed
            pass
    
    def parse_repo(self) -> float:
        """Parse all Python files in repo, return parse time in ms."""
        start = time.time()
        
        self.collect_python_files()
        for file_path in self.python_files:
            self.parse_file(file_path)
        
        # Build file index for better edge mapping
        file_index = {}
        for file_path in self.python_files:
            rel_path = file_path.relative_to(self.repo_path).as_posix()
            
            # Index by full module path
            module_name = rel_path.replace('/', '.').replace(os.sep, '.').replace('.py', '')
            file_index[module_name] = rel_path
            
            # Index by directory (package)
            parent_dir = str(Path(rel_path).parent).replace(os.sep, '.').replace('.', '', 1) if str(Path(rel_path).parent) != '.' else ''
            if parent_dir:
                file_index[parent_dir] = rel_path
            
            # Index by filename stem
            filename_base = Path(rel_path).stem
            if filename_base and filename_base != '__init__':
                if filename_base not in file_index:
                    file_index[filename_base] = rel_path
        
        # Rebuild edges with improved import-to-file mapping
        seen_edges = set()
        for source_rel, symbol_data in self.symbols.items():
            for imp in symbol_data['imports']:
                candidates = [
                    file_index.get(imp),
                    file_index.get(imp.split('.')[0]),
                ]
                for target_rel in candidates:
                    if target_rel and target_rel != source_rel:
                        edge_key = (source_rel, target_rel)
                        if edge_key not in seen_edges:
                            self.edges.append({
                                "source": source_rel,
                                "target": target_rel,
                                "type": "import"
                            })
                            seen_edges.add(edge_key)
                        break
        
        self.parse_time_ms = (time.time() - start) * 1000
        return self.parse_time_ms
    
    def to_dict(self) -> Dict[str, Any]:
        """Export graph as dictionary."""
        return {
            "symbols": self.symbols,
            "edges": self.edges,
            "metadata": {
                "parse_time_ms": round(self.parse_time_ms, 2),
                "python_files_parsed": len(self.python_files),
                "total_symbols": len(self.symbols),
            }
        }
    
    def save_json(self, output_path: str) -> int:
        """Save graph to JSON file, return size in bytes."""
        output_dict = self.to_dict()
        json_str = json.dumps(output_dict, indent=2)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        size_bytes = len(json_str.encode('utf-8'))
        return size_bytes


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python symbol_graph.py <repo_path> [output_json_path]")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else f"symbol_graph_{Path(repo_path).name}.json"
    
    if not Path(repo_path).exists():
        print(f"Error: Repository path not found: {repo_path}")
        sys.exit(1)
    
    # Parse repository
    parser = SymbolGraphParser(repo_path)
    parse_time = parser.parse_repo()
    
    # Save output
    output_size = parser.save_json(output_path)
    
    # Report results
    print(f"Repository: {repo_path}")
    print(f"Python files parsed: {len(parser.python_files)}")
    print(f"Parse time: {parse_time:.2f}ms")
    print(f"Output size: {output_size} bytes ({output_size / 1024:.1f}KB)")
    print(f"Symbols extracted: {len(parser.symbols)}")
    print(f"Edges extracted: {len(parser.edges)}")
    print(f"Output saved to: {output_path}")
    
    # Sample output
    if parser.symbols:
        sample_file = next(iter(parser.symbols.keys()))
        print(f"\nSample symbol entry ({sample_file}):")
        print(json.dumps({sample_file: parser.symbols[sample_file]}, indent=2)[:300] + "...")


if __name__ == '__main__':
    main()
