import json
import os
import sys

from tools.shared import make_preview, parse_python_file, summarize_json_value

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None


def detect_file_type(target):
    lower_target = target.lower()
    if lower_target.endswith(".py"):
        return "python"
    if lower_target.endswith(".json"):
        return "json"
    if lower_target.endswith((".yml", ".yaml")):
        return "yaml"
    if lower_target.endswith(".toml"):
        return "toml"

    base_name = os.path.basename(lower_target)
    if base_name == ".env" or base_name.startswith(".env."):
        return "env"
    return "text"


def summarize_json_file(content, target):
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        return {
            "parse_status": "fallback",
            "summary": "JSON file could not be parsed cleanly.",
            "parse_error": str(exc),
        }

    result = {
        "parse_status": "parsed",
        "summary": "JSON file",
        "json_shape": summarize_json_value(data),
    }

    if isinstance(data, dict):
        top_level_keys = list(data.keys())
        result["top_level_keys"] = top_level_keys
        if target.endswith("package.json"):
            scripts = data.get("scripts", {})
            dependencies = data.get("dependencies", {})
            dev_dependencies = data.get("devDependencies", {})
            peer_dependencies = data.get("peerDependencies", {})
            optional_dependencies = data.get("optionalDependencies", {})
            result.update(
                {
                    "summary": "Node package manifest",
                    "package_name": data.get("name"),
                    "package_version": data.get("version"),
                    "script_keys": sorted(scripts.keys()) if isinstance(scripts, dict) else [],
                    "dependency_counts": {
                        "dependencies": len(dependencies) if isinstance(dependencies, dict) else 0,
                        "devDependencies": len(dev_dependencies) if isinstance(dev_dependencies, dict) else 0,
                        "peerDependencies": len(peer_dependencies) if isinstance(peer_dependencies, dict) else 0,
                        "optionalDependencies": len(optional_dependencies) if isinstance(optional_dependencies, dict) else 0,
                    },
                }
            )
    elif isinstance(data, list):
        result["summary"] = "JSON array"

    return result


def extract_toml_sections(content):
    sections = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            sections.append(line.strip("[]"))
    return sections


def summarize_toml_file(content):
    if tomllib is None:
        return {
            "parse_status": "fallback",
            "summary": "TOML file (tomllib unavailable)",
            "section_names": extract_toml_sections(content),
        }

    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError as exc:
        return {
            "parse_status": "fallback",
            "summary": "TOML file could not be parsed cleanly.",
            "parse_error": str(exc),
            "section_names": extract_toml_sections(content),
        }

    return {
        "parse_status": "parsed",
        "summary": "TOML configuration file",
        "top_level_keys": list(data.keys()),
        "section_names": extract_toml_sections(content),
    }


def mask_secret_value(value):
    if not value:
        return ""
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + ("*" * (len(value) - 4)) + value[-2:]


def summarize_env_file(content):
    variable_names = []
    masked_values = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        variable_names.append(key)
        masked_values[key] = mask_secret_value(value.strip())

    return {
        "parse_status": "parsed",
        "summary": "Environment variable file",
        "variable_names": variable_names,
        "variable_count": len(variable_names),
        "masked_values": masked_values,
    }


def summarize_yaml_file(content):
    top_level_keys = []
    list_section_names = []
    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent == 0 and ":" in stripped:
            key = stripped.split(":", 1)[0].strip()
            if key:
                top_level_keys.append(key)
        elif indent == 0 and stripped.startswith("-"):
            list_section_names.append(stripped[:60])

    result = {
        "parse_status": "parsed-shallow",
        "summary": "YAML configuration file",
        "top_level_keys": top_level_keys,
    }
    if list_section_names:
        result["top_level_list_entries"] = list_section_names[:5]
    return result


def summarize_structured_file(file_type, content, target):
    if file_type == "json":
        return summarize_json_file(content, target)
    if file_type == "yaml":
        return summarize_yaml_file(content)
    if file_type == "toml":
        return summarize_toml_file(content)
    if file_type == "env":
        return summarize_env_file(content)
    return None


def cmd_ai_read(repo_path, target):
    path = os.path.join(repo_path, target)
    if not os.path.exists(path):
        print(f"ERROR: file not found: {target}", file=sys.stderr)
        return 2, {"error": "file_not_found", "target": target}

    content = None
    for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
        try:
            with open(path, encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue

    if content is None:
        with open(path, "rb") as f:
            content = f.read().decode("latin-1", errors="replace")

    line_count = len(content.splitlines())
    file_type = detect_file_type(target)

    if file_type == "python":
        imports, classes, functions = parse_python_file(content)
        summary = {
            "path": target,
            "file_type": file_type,
            "line_count": line_count,
            "imports": imports,
            "classes": classes,
            "functions": functions,
            "preview": make_preview(content),
        }
    else:
        summary = {
            "path": target,
            "file_type": file_type,
            "line_count": line_count,
            "preview": make_preview(content),
        }
        structured_summary = summarize_structured_file(file_type, content, target)
        if structured_summary:
            summary.update(structured_summary)

    print(json.dumps(summary))
    return 0, summary
