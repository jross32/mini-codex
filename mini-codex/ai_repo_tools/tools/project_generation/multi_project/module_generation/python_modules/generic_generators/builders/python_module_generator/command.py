"""
python_module_generator - Generate Python module code from JSON specifications (DOMAIN-AGNOSTIC)

This tool generates any Python module structure from pure JSON specs - works for:
- RPG games (Character, Monster classes)
- Web apps (Request, Response handlers)
- Data pipelines (ETL, DataProcessor classes)
- ML systems (Model, Trainer classes)
- Anything that needs Python code generation

Category: execution
Returns: success, files_written, module_paths, summary, elapsed_ms
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _generate_class_code(class_spec: Dict) -> str:
    """Generate a Python class definition from spec."""
    name = class_spec.get("name", "UnnamedClass")
    docstring = class_spec.get("docstring", "")
    methods = class_spec.get("methods", [])
    attributes = class_spec.get("attributes", [])
    
    lines = [f"class {name}:"]
    if docstring:
        lines.append(f'    """{docstring}"""')
    
    # __init__ method
    if attributes:
        init_params = ", ".join([f"{attr['name']}" for attr in attributes])
        lines.append(f"    def __init__(self, {init_params}):")
        for attr in attributes:
            lines.append(f"        self.{attr['name']} = {attr['name']}")
    else:
        lines.append("    def __init__(self):")
        lines.append("        pass")
    
    # Other methods
    for method in methods:
        method_name = method.get("name", "method")
        method_docstring = method.get("docstring", "")
        method_code = method.get("code", "pass")
        
        lines.append("")
        lines.append(f"    def {method_name}(self):")
        if method_docstring:
            lines.append(f'        """{method_docstring}"""')
        # Indent the code
        for code_line in method_code.split("\n"):
            if code_line.strip():
                lines.append(f"        {code_line}")
            else:
                lines.append("")
    
    return "\n".join(lines) + "\n"


def _generate_function_code(func_spec: Dict) -> str:
    """Generate a Python function definition from spec."""
    name = func_spec.get("name", "unnamed_func")
    docstring = func_spec.get("docstring", "")
    params = func_spec.get("params", [])
    code = func_spec.get("code", "pass")
    
    param_str = ", ".join(params) if params else ""
    lines = [f"def {name}({param_str}):"]
    if docstring:
        lines.append(f'    """{docstring}"""')
    
    for code_line in code.split("\n"):
        if code_line.strip():
            lines.append(f"    {code_line}")
        else:
            lines.append("")
    
    return "\n".join(lines) + "\n"


def _generate_module_code(module_spec: Dict) -> str:
    """Generate a complete Python module from spec."""
    docstring = module_spec.get("docstring", "")
    imports = module_spec.get("imports", [])
    classes = module_spec.get("classes", [])
    functions = module_spec.get("functions", [])
    
    lines = []
    
    if docstring:
        lines.append(f'"""{docstring}"""')
    
    # Imports
    for imp in imports:
        lines.append(imp)
    
    if imports:
        lines.append("")
    
    # Classes
    for class_spec in classes:
        lines.append(_generate_class_code(class_spec))
        lines.append("")
    
    # Functions
    for func_spec in functions:
        lines.append(_generate_function_code(func_spec))
        lines.append("")
    
    return "\n".join(lines)


def run_python_module_generator(repo_path: str, module_spec_json: Optional[str] = None) -> Tuple[int, Dict]:
    """
    Generate Python module code from JSON specifications.
    Works for ANY project domain: games, web apps, data pipelines, ML systems, etc.
    
    module_spec_json format:
    {
      "base_dir": "src",
      "modules": [
        {
          "path": "entities/npc.py",
          "docstring": "NPC system (works for RPG OR Cyberpunk OR any sim)",
          "imports": ["import json", "from enum import Enum"],
          "classes": [{
            "name": "NPC",
            "docstring": "Non-player character entity",
            "attributes": [{"name": "name"}, {"name": "faction"}, {"name": "reputation"}],
            "methods": [
              {"name": "greet", "code": "return f'Hello, I am {self.name}'"},
              {"name": "update_faction", "code": "self.faction = faction"}
            ]
          }],
          "functions": [{"name": "create_npc", "code": "return NPC('Guard', 'Corp')"}]
        }
      ]
    }
    
    Examples that work with this same tool:
    - RPG.GameState with level/experience
    - Cyberpunk.Hacker with faction/rep  
    - WebApp.RequestHandler with route/middleware
    - Pipeline.ETLJob with input_schema/transform_func
    
    Returns: success, files_written, module_paths, summary, elapsed_ms
    """
    t0 = time.monotonic()
    
    if not module_spec_json:
        return 2, {
            "success": False,
            "files_written": [],
            "module_paths": [],
            "errors": ["module_spec_json is required"],
            "summary": "No spec provided",
            "elapsed_ms": 0
        }
    
    try:
        spec = json.loads(module_spec_json)
    except json.JSONDecodeError as e:
        return 2, {
            "success": False,
            "files_written": [],
            "module_paths": [],
            "errors": [f"Invalid JSON: {str(e)}"],
            "summary": "JSON parse error",
            "elapsed_ms": 0
        }
    
    base_dir = spec.get("base_dir", "aish_tests")
    modules = spec.get("modules", [])
    
    repo_path_obj = Path(repo_path)
    base_path = repo_path_obj / base_dir
    
    files_written = []
    module_paths = []
    errors: List[str] = []
    
    for module_spec in modules:
        module_path = module_spec.get("path", "unnamed.py")
        full_path = base_path / module_path
        
        try:
            # Create parent directory if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate module code
            code = _generate_module_code(module_spec)
            
            # Write to file
            full_path.write_text(code, encoding="utf-8")
            files_written.append(str(module_path))
            module_paths.append(str(full_path.relative_to(repo_path_obj)))
        except Exception as e:
            errors.append(f"Failed to write {module_path}: {str(e)}")
    
    success = len(errors) == 0
    payload = {
        "success": success,
        "files_written": files_written,
        "module_paths": module_paths,
        "errors": errors,
        "summary": f"Generated {len(files_written)} Python modules" + (f". Errors: {len(errors)}" if errors else "."),
        "elapsed_ms": round((time.monotonic() - t0) * 1000)
    }
    
    return 0 if success else 1, payload


def cmd_python_module_generator(repo_path: str, module_spec_json: Optional[str] = None):
    code, payload = run_python_module_generator(repo_path, module_spec_json=module_spec_json)
    print(json.dumps(payload))
    return code, payload
