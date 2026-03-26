import ast
import json
import os


def get_python_module_parts(path):
    path_no_ext = path[:-3] if path.endswith(".py") else path
    parts = [part for part in path_no_ext.split("/") if part]
    if parts and parts[-1] == "__init__":
        return parts[:-1]
    return parts


def build_module_index(paths):
    index = {}
    for path in paths:
        module_parts = get_python_module_parts(path)
        if not module_parts:
            continue
        dotted = ".".join(module_parts)
        for offset in range(len(module_parts)):
            suffix = ".".join(module_parts[offset:])
            index.setdefault(suffix, []).append(path)
        index.setdefault(dotted, []).append(path)
    return index


def extract_import_references(last_read_file, content):
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    module_parts = get_python_module_parts(last_read_file)
    if os.path.basename(last_read_file) == "__init__.py":
        current_package = module_parts
    else:
        current_package = module_parts[:-1]
    references = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    references.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            base_parts = list(current_package) if node.level else []
            if node.level:
                trim = max(node.level - 1, 0)
                if trim:
                    base_parts = base_parts[:-trim]
            if node.module:
                base_parts.extend([part for part in node.module.split(".") if part])

            if base_parts:
                references.append(".".join(base_parts))
            for alias in node.names:
                if alias.name == "*":
                    continue
                alias_parts = list(base_parts)
                alias_parts.append(alias.name)
                references.append(".".join([part for part in alias_parts if part]))

    ordered = []
    seen = set()
    for reference in references:
        if reference and reference not in seen:
            seen.add(reference)
            ordered.append(reference)
    return ordered


def resolve_import_candidates(import_references, module_index):
    resolved = []
    seen = set()

    for reference in import_references:
        search_terms = [reference]
        if "." in reference:
            search_terms.append(reference.rsplit(".", 1)[0])

        for term in search_terms:
            for candidate in module_index.get(term, []):
                if candidate not in seen:
                    seen.add(candidate)
                    resolved.append(candidate)
    return resolved


def is_test_file(path):
    name = os.path.basename(path)
    return "/tests/" in f"/{path}" or name.startswith("test_") or name.endswith("_test.py")


def is_noise_file(path):
    noise_prefixes = (
        "alembic/",
        "migrations/",
        "tools/",
        "scripts/",
        ".egg-info/",
        "__pycache__/",
        ".venv/",
        "venv/",
        "node_modules/",
        "site-packages/",
    )
    return any(path.startswith(prefix) or f"/{prefix}" in f"/{path}" for prefix in noise_prefixes)


def is_weak_candidate(path):
    weak_names = {"conftest.py", "setup.py", "manage.py"}
    return os.path.basename(path) in weak_names


def is_concrete_impl_candidate(path, import_candidates):
    if os.path.basename(path) == "__init__.py":
        return False
    if is_test_file(path):
        return False

    concrete_names = {
        "models.py",
        "model.py",
        "auth.py",
        "main.py",
        "routes.py",
        "service.py",
        "services.py",
        "config.py",
        "db.py",
        "database.py",
    }
    name = os.path.basename(path)
    if is_weak_candidate(path):
        return False
    return path in import_candidates or name in concrete_names or path.endswith(".py")


def build_test_pair_targets(path):
    directory = path.rsplit("/", 1)[0] if "/" in path else ""
    name = os.path.basename(path)
    stem = name[:-3] if name.endswith(".py") else name
    candidates = []

    if is_test_file(path):
        impl_stem = stem
        if impl_stem.startswith("test_"):
            impl_stem = impl_stem[len("test_"):]
        if impl_stem.endswith("_test"):
            impl_stem = impl_stem[:-5]
        parent_dir = directory
        if parent_dir.endswith("/tests"):
            parent_dir = parent_dir[:-6]
        if parent_dir:
            candidates.append(f"{parent_dir}/{impl_stem}.py")
        else:
            candidates.append(f"{impl_stem}.py")
    else:
        test_name = f"test_{stem}.py"
        if directory:
            candidates.extend(
                [
                    f"{directory}/{test_name}",
                    f"{directory}/tests/{test_name}",
                    f"{directory}/test_{stem}.py",
                ]
            )
            parent_dir = directory.rsplit("/", 1)[0] if "/" in directory else ""
            if parent_dir:
                candidates.append(f"{parent_dir}/tests/{test_name}")
        else:
            candidates.append(test_name)

    ordered = []
    seen = set()
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    return ordered


def score_candidate(path, last_read_file, import_candidates, test_pair_targets, has_concrete_alternative):
    score = 0
    reasons = []
    name = os.path.basename(path)
    candidate_dir = path.rsplit("/", 1)[0] if "/" in path else ""
    last_dir = last_read_file.rsplit("/", 1)[0] if "/" in last_read_file else ""

    if path in import_candidates:
        score += 120
        reasons.append("imported by last-read file")

    if last_read_file and candidate_dir == last_dir:
        score += 30
        reasons.append("same directory")

    if path in test_pair_targets:
        score += 70
        reasons.append("test/implementation pair")

    if is_test_file(path):
        if is_test_file(last_read_file):
            score -= 10
        else:
            score -= 25
            reasons.append("test file kept lower unless paired")
    else:
        score += 20
        reasons.append("implementation file")

    if name in {"app.py", "main.py"}:
        score += 12
        reasons.append("likely entry or service module")
    elif name == "__init__.py":
        score -= 8
        reasons.append("package initializer")
        if has_concrete_alternative:
            score -= 120
            reasons.append("deprioritized vs concrete module")

    if is_weak_candidate(path):
        score -= 20
        reasons.append("weak support file")

    if "/" not in path:
        score -= 5

    return score, reasons


def build_recommendations(important_files, last_read_file, import_candidates, test_pair_targets):
    scored = []
    last_dir = last_read_file.rsplit("/", 1)[0] if "/" in last_read_file else ""
    has_concrete_alternative = any(
        (path.rsplit("/", 1)[0] if "/" in path else "") == last_dir
        and is_concrete_impl_candidate(path, import_candidates)
        for path in important_files
    )

    for path in important_files:
        if path == last_read_file:
            continue
        score, reasons = score_candidate(
            path,
            last_read_file,
            import_candidates,
            test_pair_targets,
            has_concrete_alternative,
        )
        scored.append((score, path, reasons))

    scored.sort(key=lambda item: (-item[0], item[1]))

    recommendations = []
    for score, path, reasons in scored[:3]:
        reason_text = "; ".join(reasons[:3]) if reasons else "related module"
        recommendations.append({"file": path, "reason": reason_text})
    return recommendations


def cmd_test_select(repo_path, read_files_json="", last_read_file=""):
    read_files = set()
    try:
        if read_files_json:
            read_files = set(json.loads(read_files_json))
    except (json.JSONDecodeError, ValueError):
        pass

    all_files = []
    for root, dirs, filenames in os.walk(repo_path):
        if root.startswith(os.path.join(repo_path, "ai_repo_tools")) or root.startswith(os.path.join(repo_path, "agent")):
            continue
        for name in filenames:
            if name.startswith("."):
                continue
            path = os.path.relpath(os.path.join(root, name), repo_path)
            all_files.append(path.replace("\\", "/"))

    all_py = [f for f in all_files if f.endswith(".py")]
    unread_py = [f for f in all_py if f not in read_files]
    important_files = [f for f in unread_py if not is_noise_file(f)]

    import_candidates = set()
    if last_read_file and last_read_file.endswith(".py"):
        last_read_path = os.path.join(repo_path, last_read_file)
        if os.path.exists(last_read_path):
            try:
                with open(last_read_path, encoding="utf-8") as f:
                    last_content = f.read()
            except UnicodeDecodeError:
                with open(last_read_path, encoding="latin-1") as f:
                    last_content = f.read()
            import_refs = extract_import_references(last_read_file, last_content)
            module_index = build_module_index([f for f in all_py if not is_noise_file(f)])
            import_candidates = set(resolve_import_candidates(import_refs, module_index))

    test_pair_targets = set(build_test_pair_targets(last_read_file)) if last_read_file else set()
    recommendations = build_recommendations(important_files, last_read_file, import_candidates, test_pair_targets)

    result = {
        "recommended_files": recommendations[:3],
        "all_unread_count": len(important_files),
        "read_count": len(read_files),
        "summary": f"Found {len(recommendations)} recommended files out of {len(important_files)} unread.",
    }
    print(json.dumps(result))
    return 0, result
