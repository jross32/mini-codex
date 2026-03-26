from __future__ import annotations

from typing import Dict, List


COMMON_ARGS = [
    {"name": "query", "type": "str", "optional": True},
    {"name": "limit", "type": "int", "optional": True, "default": 50},
]


def _spec(name: str, category: str, description: str, handler: str, **config) -> Dict:
    return {
        "name": name,
        "category": category,
        "description": description,
        "handler": handler,
        "args": COMMON_ARGS,
        "returns": config.pop(
            "returns",
            "success, tool, category, handler, matches, count, summary, elapsed_ms",
        ),
        **config,
    }


TOOL_CATALOG: List[Dict] = [
    # discovery (20)
    _spec("python_file_locator", "discovery", "Locate Python files in the repo", "glob_locator", patterns=["*.py"]),
    _spec("json_file_locator", "discovery", "Locate JSON files in the repo", "glob_locator", patterns=["*.json"]),
    _spec("yaml_file_locator", "discovery", "Locate YAML files in the repo", "glob_locator", patterns=["*.yml", "*.yaml"]),
    _spec("markdown_file_locator", "discovery", "Locate Markdown files in the repo", "glob_locator", patterns=["*.md"]),
    _spec("test_file_locator", "discovery", "Locate Python test files", "glob_locator", patterns=["test_*.py", "*_test.py"]),
    _spec("readme_locator", "discovery", "Find README-style files", "filename_matcher", needles=["readme"]),
    _spec("config_file_locator", "discovery", "Find configuration and settings files", "filename_matcher", needles=["config", "settings", "pyproject", "requirements", ".env", "package.json"]),
    _spec("large_file_finder", "discovery", "Find the largest files in the repo", "large_file_finder"),
    _spec("empty_dir_finder", "discovery", "Find empty directories", "empty_dir_finder"),
    _spec("duplicate_name_finder", "discovery", "Find duplicate file names across directories", "duplicate_name_finder"),
    _spec("extension_breakdown", "discovery", "Count files by extension", "extension_breakdown"),
    _spec("todo_finder", "discovery", "Find TODO markers in source files", "text_search", terms=["TODO"]),
    _spec("fixme_finder", "discovery", "Find FIXME markers in source files", "text_search", terms=["FIXME"]),
    _spec("import_name_finder", "discovery", "Find Python import names and where they appear", "python_symbol_finder", symbol_mode="imports"),
    _spec("class_name_finder", "discovery", "Find Python class names", "python_symbol_finder", symbol_mode="classes"),
    _spec("function_name_finder", "discovery", "Find Python function names", "python_symbol_finder", symbol_mode="functions"),
    _spec("binary_file_locator", "discovery", "Locate likely binary files", "binary_file_locator"),
    _spec("long_path_finder", "discovery", "Find very long file paths", "long_path_finder"),
    _spec("recent_file_finder", "discovery", "Find most recently modified files", "recent_file_finder"),
    _spec("shell_script_locator", "discovery", "Locate shell and PowerShell scripts", "glob_locator", patterns=["*.sh", "*.ps1", "*.bat", "*.cmd"]),

    # planning (15)
    _spec("reading_queue_planner", "planning", "Recommend a reading order for understanding the repo", "planner_by_patterns", patterns=["README*", "*.md", "*.py"]),
    _spec("test_focus_planner", "planning", "Recommend test files to inspect first", "planner_by_patterns", patterns=["test_*.py", "*_test.py", "tests/*"]),
    _spec("refactor_candidate_planner", "planning", "Identify large files that are likely refactor candidates", "refactor_candidate_planner"),
    _spec("config_review_planner", "planning", "Recommend configuration files for review", "config_review_planner", patterns=["*.json", "*.yml", "*.yaml", "pyproject.toml", "requirements*.txt", ".env*"]),
    _spec("doc_gap_planner", "planning", "Identify code-heavy areas with little nearby documentation", "doc_gap_planner"),
    _spec("dead_code_review_planner", "planning", "Identify likely dead-code review targets", "dead_code_review_planner"),
    _spec("dependency_cleanup_planner", "planning", "Recommend dependency-related files for cleanup review", "dependency_cleanup_planner", patterns=["requirements*.txt", "pyproject.toml", "setup.py", "package.json"]),
    _spec("logging_improvement_planner", "planning", "Find files that likely need logging cleanup", "logging_improvement_planner", terms=["print(", "logging.", "logger."] ),
    _spec("error_handling_review_planner", "planning", "Find files with error handling to review", "error_handling_review_planner", terms=["try:", "except ", "raise "] ),
    _spec("model_layer_review_planner", "planning", "Find model and schema related files", "model_layer_review_planner", needles=["model", "schema", "entity"]),
    _spec("auth_review_planner", "planning", "Find authentication and authorization related files", "auth_review_planner", needles=["auth", "login", "permission", "session", "token"]),
    _spec("api_surface_planner", "planning", "Find route, endpoint, and handler files", "api_surface_planner", needles=["api", "route", "endpoint", "handler", "controller"]),
    _spec("frontend_review_planner", "planning", "Find frontend-facing files to review", "frontend_review_planner", patterns=["*.html", "*.css", "*.js", "*.ts", "*.jsx", "*.tsx"]),
    _spec("migration_risk_planner", "planning", "Find migration and schema evolution files", "migration_risk_planner", needles=["migration", "migrate", "alembic", "schema"]),
    _spec("hotspot_review_planner", "planning", "Combine size and recency to find review hotspots", "hotspot_review_planner_plus"),

    # evaluation (20)
    _spec("python_file_count_score", "evaluation", "Score the repo based on Python file volume", "score_python_file_count"),
    _spec("test_density_score", "evaluation", "Estimate how test-heavy the repo is", "score_test_density"),
    _spec("docstring_coverage_estimator", "evaluation", "Estimate Python docstring coverage", "score_docstring_coverage"),
    _spec("todo_density_score", "evaluation", "Estimate TODO density across source files", "score_todo_density"),
    _spec("config_sprawl_score", "evaluation", "Score configuration sprawl risk", "score_config_sprawl_plus"),
    _spec("import_complexity_score", "evaluation", "Estimate import surface complexity", "score_import_complexity_plus"),
    _spec("file_size_risk_score", "evaluation", "Score risk based on oversized files", "score_file_size_risk_plus"),
    _spec("long_function_risk_score", "evaluation", "Estimate risk from long Python functions", "score_long_function_risk_plus"),
    _spec("duplicate_name_risk_score", "evaluation", "Score ambiguity caused by duplicate file names", "score_duplicate_name_risk_plus"),
    _spec("repo_freshness_score", "evaluation", "Estimate freshness from recent file changes", "score_repo_freshness"),
    _spec("module_balance_score", "evaluation", "Measure file-extension balance across the repo", "score_module_balance_plus"),
    _spec("log_noise_score", "evaluation", "Estimate noise caused by log files", "score_log_noise"),
    _spec("dependency_surface_score", "evaluation", "Estimate the size of the dependency surface", "score_dependency_surface_plus"),
    _spec("test_presence_check", "evaluation", "Check whether the repo includes tests", "boolean_check", check_name="tests_present"),
    _spec("readme_presence_check", "evaluation", "Check whether the repo includes a README", "boolean_check", check_name="readme_present"),
    _spec("entrypoint_health_check", "evaluation", "Check whether the repo exposes likely entrypoints", "boolean_check", check_name="entrypoints_present"),
    _spec("json_validity_sampler", "evaluation", "Sample JSON files and report parse health", "structured_validity_sampler", parse_mode="json"),
    _spec("yaml_validity_sampler", "evaluation", "Sample YAML files and report parse health", "structured_validity_sampler", parse_mode="yaml"),
    _spec("python_syntax_sampler", "evaluation", "Sample Python files and report syntax health", "python_syntax_sampler"),
    _spec("change_risk_snapshot", "evaluation", "Produce a lightweight composite repo risk snapshot", "change_risk_snapshot_plus"),

    # reading (20)
    _spec("json_summary_reader", "reading", "Summarize JSON files", "json_summary_reader_plus", read_mode="json"),
    _spec("yaml_summary_reader", "reading", "Summarize YAML files", "structured_reader", read_mode="yaml"),
    _spec("csv_summary_reader", "reading", "Summarize CSV files", "structured_reader", read_mode="csv"),
    _spec("text_excerpt_reader", "reading", "Read plain text excerpts", "structured_reader", read_mode="text"),
    _spec("markdown_heading_reader", "reading", "Read Markdown heading structure", "structured_reader", read_mode="markdown"),
    _spec("python_symbol_reader", "reading", "Summarize Python imports, classes, and functions", "structured_reader", read_mode="python_symbols"),
    _spec("imports_reader", "reading", "Read Python import statements", "structured_reader", read_mode="python_imports"),
    _spec("function_list_reader", "reading", "Read Python function names", "structured_reader", read_mode="python_functions"),
    _spec("class_list_reader", "reading", "Read Python class names", "structured_reader", read_mode="python_classes"),
    _spec("env_key_reader", "reading", "Read keys from .env files", "structured_reader", read_mode="env"),
    _spec("ini_summary_reader", "reading", "Summarize INI files", "structured_reader", read_mode="ini"),
    _spec("toml_summary_reader", "reading", "Summarize TOML files", "structured_reader", read_mode="toml"),
    _spec("requirements_reader", "reading", "Read Python requirements files", "requirements_reader_plus", read_mode="requirements"),
    _spec("changelog_reader", "reading", "Read changelog-style files", "structured_reader", read_mode="changelog"),
    _spec("license_reader", "reading", "Read license files", "structured_reader", read_mode="license"),
    _spec("dockerfile_reader", "reading", "Read Dockerfiles", "structured_reader", read_mode="dockerfile"),
    _spec("compose_reader", "reading", "Read compose YAML files", "structured_reader", read_mode="compose"),
    _spec("package_json_reader", "reading", "Read package.json summaries", "structured_reader", read_mode="package_json"),
    _spec("notebook_cell_counter", "reading", "Count notebook cells in .ipynb files", "structured_reader", read_mode="notebook"),
    _spec("log_summary_reader", "reading", "Summarize log files", "structured_reader", read_mode="log"),

    # execution (10)
    _spec("python_compile_batch", "execution", "Compile Python files to check syntax in batch", "execution_probe", probe_mode="python_compile"),
    _spec("pytest_collection_probe", "execution", "Probe pytest-style test collection by scanning names", "execution_probe", probe_mode="pytest_collection"),
    _spec("script_entrypoint_probe", "execution", "Probe for Python script entrypoints", "execution_probe", probe_mode="script_entrypoints"),
    _spec("module_resolution_probe", "execution", "Probe local Python module resolution candidates", "execution_probe", probe_mode="module_resolution"),
    _spec("json_parse_batch", "execution", "Parse JSON files in batch", "execution_probe", probe_mode="json_parse"),
    _spec("yaml_parse_batch", "execution", "Parse YAML files in batch", "execution_probe", probe_mode="yaml_parse"),
    _spec("command_catalog_probe", "execution", "Probe the registered tool catalog", "execution_probe", probe_mode="command_catalog"),
    _spec("notebook_parse_probe", "execution", "Probe notebook parseability", "execution_probe", probe_mode="notebook_parse"),
    _spec("shell_script_probe", "execution", "Probe shell scripts for presence and size", "execution_probe", probe_mode="shell_scripts"),
    _spec("python_entrypoint_probe", "execution", "Probe common Python app entrypoints", "execution_probe", probe_mode="python_entrypoints"),

    # health (15)
    _spec("missing_readme_check", "health", "Find top-level projects missing a README", "health_scan", scan_mode="missing_readme"),
    _spec("missing_init_check", "health", "Find Python packages missing __init__.py", "health_scan", scan_mode="missing_init"),
    _spec("trailing_whitespace_check", "health", "Find files with trailing whitespace", "health_scan", scan_mode="trailing_whitespace"),
    _spec("large_log_check", "health", "Find oversized log files", "health_scan", scan_mode="large_logs"),
    _spec("hardcoded_secret_scan", "health", "Find likely hardcoded secrets", "health_scan", scan_mode="hardcoded_secrets"),
    _spec("debug_statement_scan", "health", "Find debug-style print and breakpoint statements", "health_scan", scan_mode="debug_statements"),
    _spec("empty_file_check", "health", "Find empty files", "health_scan", scan_mode="empty_files"),
    _spec("line_length_scan", "health", "Find lines exceeding a typical length threshold", "health_scan", scan_mode="line_length"),
    _spec("tab_indent_scan", "health", "Find files using hard tab indentation", "health_scan", scan_mode="tab_indent"),
    _spec("mixed_newline_scan", "health", "Find files with mixed newline styles", "health_scan", scan_mode="mixed_newlines"),
    _spec("broken_symlink_check", "health", "Find broken symlinks", "health_scan", scan_mode="broken_symlinks"),
    _spec("virtualenv_leak_check", "health", "Find embedded virtualenv directories", "health_scan", scan_mode="virtualenv_leak"),
    _spec("temp_file_scan", "health", "Find temporary or editor backup files", "health_scan", scan_mode="temp_files"),
    _spec("cache_dir_scan", "health", "Find cache directories", "health_scan", scan_mode="cache_dirs"),
    _spec("duplicate_test_name_scan", "health", "Find duplicate Python test function names", "health_scan", scan_mode="duplicate_test_names"),
]


CATALOG_BY_NAME = {spec["name"]: spec for spec in TOOL_CATALOG}


_EXPANSION_BLUEPRINTS = [
    {
        "name_template": "networking_query_probe_{n:03d}",
        "category": "networking",
        "description_template": "Probe network diagnostics for query-driven slice #{n}",
        "handler": "query_network_probe",
    },
    {
        "name_template": "discovery_query_locator_{n:03d}",
        "category": "discovery",
        "description_template": "Locate files related to a query-driven discovery slice #{n}",
        "handler": "query_locator",
    },
    {
        "name_template": "planning_query_planner_{n:03d}",
        "category": "planning",
        "description_template": "Plan review targets for query-driven slice #{n}",
        "handler": "query_planner",
    },
    {
        "name_template": "evaluation_query_score_{n:03d}",
        "category": "evaluation",
        "description_template": "Score risk for query-driven slice #{n}",
        "handler": "query_risk_score",
    },
    {
        "name_template": "reading_query_reader_{n:03d}",
        "category": "reading",
        "description_template": "Read focused excerpts for query-driven slice #{n}",
        "handler": "query_excerpt_reader",
    },
    {
        "name_template": "execution_query_probe_{n:03d}",
        "category": "execution",
        "description_template": "Probe parse and entrypoint signals for query-driven slice #{n}",
        "handler": "query_parse_probe",
    },
    {
        "name_template": "health_query_scan_{n:03d}",
        "category": "health",
        "description_template": "Scan health issues for query-driven slice #{n}",
        "handler": "query_health_scan",
    },
]


def build_tool_catalog(target_count: int | None = None) -> List[Dict]:
    if target_count is None or target_count <= len(TOOL_CATALOG):
        return list(TOOL_CATALOG if target_count is None else TOOL_CATALOG[:target_count])

    catalog = list(TOOL_CATALOG)
    extra_needed = target_count - len(catalog)
    for offset in range(extra_needed):
        blueprint = _EXPANSION_BLUEPRINTS[offset % len(_EXPANSION_BLUEPRINTS)]
        n = (offset // len(_EXPANSION_BLUEPRINTS)) + 1
        catalog.append(
            _spec(
                blueprint["name_template"].format(n=n),
                blueprint["category"],
                blueprint["description_template"].format(n=n),
                blueprint["handler"],
            )
        )
    return catalog
