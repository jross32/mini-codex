import ast
import json


def parse_python_file(content):
    try:
        tree = ast.parse(content)
        imports = []
        classes = []
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef) and node.name != "__init__":
                functions.append(node.name)

        return imports, classes, functions
    except SyntaxError:
        return [], [], []


def make_preview(content, limit=400):
    return content[:limit]


def summarize_json_value(value):
    if isinstance(value, dict):
        return {"type": "object", "key_count": len(value)}
    if isinstance(value, list):
        item_types = sorted({type(item).__name__ for item in value[:10]})
        return {
            "type": "array",
            "item_count": len(value),
            "item_types": item_types,
        }
    return {"type": type(value).__name__, "value_preview": repr(value)[:80]}


def read_text_file_with_fallback(path):
    for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
        try:
            with open(path, encoding=encoding) as f:
                return f.read(), encoding
        except UnicodeDecodeError:
            continue
    with open(path, "rb") as f:
        return f.read().decode("latin-1", errors="replace"), "latin-1"


def parse_json_safe(content):
    try:
        return json.loads(content), None
    except json.JSONDecodeError as exc:
        return None, str(exc)
