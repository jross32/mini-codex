"""
Centralized tool registry for mini-codex ai_repo_tools.

Defines every tool's category, description, and argument spec.
Agents and CLI can query this to discover tools without executing them.

Usage:
    from tools.registry import TOOL_REGISTRY, TOOL_CATEGORIES
    print(TOOL_CATEGORIES.keys())          # all categories
    print(TOOL_REGISTRY["dep_graph"])      # metadata for one tool
"""

import json
from pathlib import Path

TOOL_CATEGORIES = {
    "discovery": {
        "description": "Understand the contents and structure of a codebase",
        "tools": ["repo_map", "fast_analyze", "dep_graph"],
    },
    "planning": {
        "description": "Decide what to read, run, and do next",
        "tools": ["fast_process", "fast_prepare"],
    },
    "evaluation": {
        "description": "Measure quality, performance, and impact of changes",
        "tools": ["fast_evaluate", "bench_compare", "diff_check", "task_trace", "friction_summarizer", "trust_trend", "git_changed_files"],
    },
    "reading": {
        "description": "Parse and extract structured content from files",
        "tools": ["ai_read", "artifact_read", "code_search"],
    },
    "execution": {
        "description": "Generic Heroes: file/module generation, batch parsing, test execution - works for ANY project type (RPG, web, pipeline, etc)",
        "tools": ["cmd_run", "python_module_generator", "directory_structure_generator", "json_parse_batch", "yaml_parse_batch", 
                  "python_compile_batch", "command_catalog_probe", "module_resolution_probe", "execution_query_probe_001", 
                  "pytest_collection_probe", "notebook_parse_probe", "python_entrypoint_probe", "script_entrypoint_probe", "shell_script_probe"],
    },
    "health": {
        "description": "Validate environment, dependencies, syntax, and logs",
        "tools": ["env_check", "test_select", "lint_check", "log_tail", "repo_health_check", "dep_readiness_check", "tool_meta_audit"],
    },
    "networking": {
        "description": "Network diagnostics and connectivity probes (defensive/observational)",
        "tools": ["dns_lookup", "reverse_dns_lookup", "http_head_probe", "tls_cert_probe", "network_interface_info"],
    },
    "toolmaker": {
        "description": "Meta-tools that audit, improve, and create other tools",
        "tools": ["tool_audit", "tool_improver", "agent_audit", "agent_improver", "toolmaker", "bulk_tool_generator"],
    },
    "game_systems": {
        "description": "Atomic tools for building RPG games - character, combat, monsters, UI, shops, persistence",
        "tools": [
            "character_name_input", "character_stat_strength_init", "character_stat_defense_init", "character_stat_wisdom_init",
            "character_hp_calculator", "character_level_initializer", "character_experience_initializer", "character_gold_initializer",
            "character_damage_formula", "character_damage_reducer_by_defense", "character_heal_limiter", "character_experience_accumulator",
            "character_level_threshold_calculator", "character_effective_levelup_check", "character_level_incrementer", "character_hp_growth_on_level",
            "character_stat_growth_on_level", "character_experience_reset_on_level", "character_state_serializer", "character_is_alive_checker",
            "character_system_generator", "combat_system_generator", "monster_system_generator", "rest_system_generator",
            "saveload_system_generator", "shop_system_generator", "ui_effects_generator", "rpg_adventure_builder", "rpg_game_builder", "game_orchestrator",
        ],
    },
}

TOOL_REGISTRY = {
    # ─── discovery ────────────────────────────────────────────────────────────
    "repo_map": {
        "category": "discovery",
        "description": "List all files in the repository, filtering noise dirs",
        "args": [],
        "returns": "list of relative file paths",
    },
    "fast_analyze": {
        "category": "discovery",
        "description": "Fast deterministic repo analysis with orientation doc references",
        "args": [{"name": "max_files", "type": "int", "optional": True}],
        "returns": "orientation_docs, top_extensions, file counts",
    },
    "dep_graph": {
        "category": "discovery",
        "description": "Python import dependency graph — which files import which others",
        "args": [{"name": "max_files", "type": "int", "optional": True}],
        "returns": "edges list and sorted importers/importees",
    },
    # ─── planning ─────────────────────────────────────────────────────────────
    "fast_process": {
        "category": "planning",
        "description": "Generate a deterministic processing plan from repository structure",
        "args": [{"name": "max_files", "type": "int", "optional": True}],
        "returns": "primary_orientation_doc, recommended_followups, planned_reads",
    },
    "fast_prepare": {
        "category": "planning",
        "description": "Generate a deterministic preflight preparation plan",
        "args": [{"name": "max_files", "type": "int", "optional": True}],
        "returns": "preparation_steps, estimated counts",
    },
    # ─── evaluation ───────────────────────────────────────────────────────────
    "fast_evaluate": {
        "category": "evaluation",
        "description": "Score repo readiness from preparation plan (0-100)",
        "args": [{"name": "max_files", "type": "int", "optional": True}],
        "returns": "score, rating (strong/good/fair/weak)",
    },
    "bench_compare": {
        "category": "evaluation",
        "description": "Compare legacy vs current fast_process path and report performance gains",
        "args": [
            {"name": "max_files", "type": "int", "optional": True},
            {"name": "runs", "type": "int", "optional": True, "default": 12},
            {"name": "warmups", "type": "int", "optional": True, "default": 1},
        ],
        "returns": "gain.mean/p95/median with multiplier and pct",
    },
    "diff_check": {
        "category": "evaluation",
        "description": "Compare two file paths and return a structured change summary",
        "args": [
            {"name": "file_a", "type": "str"},
            {"name": "file_b", "type": "str"},
        ],
        "returns": "lines_added, lines_removed, functions_changed, imports_changed",
    },
    "task_trace": {
        "category": "evaluation",
        "description": "Parse agent log files and return a structured step-by-step tool trace",
        "args": [{"name": "log_path", "type": "str", "optional": True}],
        "returns": "steps list with tool, args, outcome per step",
    },
    "friction_summarizer": {
        "category": "evaluation",
        "description": "Summarize repeated friction patterns from observation logs across repos",
        "args": [{"name": "top", "type": "int", "optional": True, "default": 20}],
        "returns": "meta summary and ranked friction patterns",
    },
    "trust_trend": {
        "category": "evaluation",
        "description": "Estimate trust-score trend across historical orchestrator worker runs",
        "args": [
            {"name": "lookback", "type": "int", "optional": True, "default": 20},
            {"name": "peers", "type": "int", "optional": True, "default": 2},
        ],
        "returns": "overall and per-worker trend signal (improving/stalling/declining)",
    },
    "git_changed_files": {
        "category": "evaluation",
        "description": "Fast summary of changed files in active git repo (staged/unstaged/untracked/conflicts)",
        "args": [],
        "returns": "counts and file lists by state plus raw porcelain entries",
    },
    # ─── reading ──────────────────────────────────────────────────────────────
    "ai_read": {
        "category": "reading",
        "description": "Parse Python and structured config files; return summary JSON",
        "args": [{"name": "path", "type": "str"}],
        "returns": "imports, classes, functions, preview, file_type",
    },
    "artifact_read": {
        "category": "reading",
        "description": "Summarize agent logs, comparison artifacts, and usage logs",
        "args": [{"name": "path", "type": "str"}],
        "returns": "artifact_type, summary, structured fields",
    },
    "code_search": {
        "category": "reading",
        "description": "Grep-like text and symbol search across the repo with structured JSON output",
        "args": [
            {"name": "pattern", "type": "str"},
            {"name": "path_filter", "type": "str", "optional": True},
            {"name": "max_results", "type": "int", "optional": True, "default": 50},
        ],
        "returns": "matches list with file, line, text",
    },
    # ─── execution ────────────────────────────────────────────────────────────
    "cmd_run": {
        "category": "execution",
        "description": "Run pytest or a Python script; return structured JSON results",
        "args": [{"name": "target", "type": "str", "optional": True}],
        "returns": "mode, exit_code, passed/failed counts, stdout/stderr excerpts",
    },
    "python_module_generator": {
        "category": "execution",
        "description": "GENERIC HERO: Generate Python module code from JSON specs (works for RPG, web, pipeline, ML - any project)",
        "args": [{"name": "module_spec_json", "type": "str", "optional": True}],
        "returns": "success, files_written, module_paths, summary, elapsed_ms",
    },
    "directory_structure_generator": {
        "category": "execution",
        "description": "GENERIC HERO: Create nested directory structures from JSON spec - works for any project layout",
        "args": [{"name": "spec_json", "type": "str", "optional": True}],
        "returns": "success, dirs_created, files_created, summary, elapsed_ms",
    },
    "json_parse_batch": {
        "category": "execution",
        "description": "Batch parse JSON files across repo",
        "args": [{"name": "query", "type": "str", "optional": True}, {"name": "limit", "type": "int", "optional": True, "default": 50}],
        "returns": "matches, count, summary, elapsed_ms",
    },
    "yaml_parse_batch": {
        "category": "execution",
        "description": "Batch parse YAML files across repo",
        "args": [{"name": "query", "type": "str", "optional": True}, {"name": "limit", "type": "int", "optional": True, "default": 50}],
        "returns": "matches, count, summary, elapsed_ms",
    },
    "python_compile_batch": {
        "category": "execution",
        "description": "Compile Python files to check syntax in batch",
        "args": [{"name": "query", "type": "str", "optional": True}, {"name": "limit", "type": "int", "optional": True, "default": 50}],
        "returns": "matches, count, summary, elapsed_ms",
    },
    "command_catalog_probe": {
        "category": "execution",
        "description": "Probe the registered tool catalog",
        "args": [{"name": "query", "type": "str", "optional": True}, {"name": "limit", "type": "int", "optional": True, "default": 50}],
        "returns": "matches, count, summary, elapsed_ms",
    },
    "python_entrypoint_probe": {
        "category": "execution",
        "description": "Probe common Python app entrypoints",
        "args": [{"name": "query", "type": "str", "optional": True}, {"name": "limit", "type": "int", "optional": True, "default": 50}],
        "returns": "matches, count, summary, elapsed_ms",
    },
    # ─── health ───────────────────────────────────────────────────────────────
    "env_check": {
        "category": "health",
        "description": "Check whether declared dependencies are importable (read-only)",
        "args": [],
        "returns": "ok list, missing list, all_ok bool",
    },
    "test_select": {
        "category": "health",
        "description": "Recommend next files to read based on already-read files",
        "args": [
            {"name": "read_files_json", "type": "str"},
            {"name": "last_read_file", "type": "str"},
        ],
        "returns": "recommended list of files to read next",
    },
    "lint_check": {
        "category": "health",
        "description": "Python syntax check and basic quality scan on one file or the whole repo",
        "args": [{"name": "target", "type": "str", "optional": True}],
        "returns": "files_checked, errors list, warnings list, all_ok bool",
    },
    "log_tail": {
        "category": "health",
        "description": "Read the last N lines of a log file and return a structured summary",
        "args": [
            {"name": "log_path", "type": "str"},
            {"name": "lines", "type": "int", "optional": True, "default": 50},
        ],
        "returns": "tail_lines, error_count, warning_count, last_tool_used",
    },
        # ─── toolmaker ────────────────────────────────────────────────────────────
        "tool_audit": {
            "category": "toolmaker",
            "description": "Scan all toolkit tools and score them on quality dimensions (0-5); return worst-first ranked list",
            "args": [
                {"name": "output_format", "type": "str", "optional": True, "default": "json"},
                {"name": "category_filter", "type": "str", "optional": True},
                {"name": "top_n", "type": "int", "optional": True, "default": 20},
            ],
            "returns": "tools_found, candidates (worst-first), perfect_tools, improvement_order, summary",
        },
        "tool_improver": {
            "category": "toolmaker",
            "description": "Apply deterministic in-place improvements to an existing tool and all associated files",
            "args": [{"name": "tool_name", "type": "str"}],
            "returns": "patches_applied, files_modified, warnings, elapsed_ms, summary",
        },
        "agent_audit": {
            "category": "toolmaker",
            "description": "Audit agent-core policy state against observed friction and propose bounded tuning recommendations",
            "args": [{"name": "mode", "type": "str", "optional": True}],
            "returns": "health_score, recommendations, summary",
        },
        "agent_improver": {
            "category": "toolmaker",
            "description": "Apply bounded policy tuning updates to the agent core state",
            "args": [{"name": "recommendations_json", "type": "str", "optional": True}],
            "returns": "applied changes, before/after core state, summary",
        },
        "toolmaker": {
            "category": "toolmaker",
            "description": "Scaffold a complete new tool from a spec and wire it into the toolkit atomically",
            "args": [
                {"name": "name", "type": "str"},
                {"name": "category", "type": "str"},
                {"name": "description", "type": "str", "optional": True},
                {"name": "args_spec_json", "type": "str", "optional": True},
                {"name": "returns_desc", "type": "str", "optional": True},
            ],
            "returns": "files_created, files_modified, errors, next_step, summary",
        },
        "bulk_tool_generator": {
            "category": "toolmaker",
            "description": "Materialize any requested count of known named tools from the built-in expandable catalog (requires explicit approval token --user-approved-generator) and remove anonymous auto tools",
            "args": [
                {"name": "count", "type": "int", "optional": True, "default": 100},
                {"name": "start_index", "type": "int", "optional": True, "default": 1},
                {"name": "replace_auto_tools", "type": "bool", "optional": True, "default": True},
            ],
            "returns": "generated_count, removed_auto_tool_count, generated_tools, seed_catalog_size, materialized_catalog_size, summary",
        },
    "repo_health_check": {
        "category": "health",
        "description": "Check repo structure health and report any issues",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "dep_readiness_check": {
        "category": "health",
        "description": "Check dependency readiness before executing tests or scripts.",
        "args": [
            {
                "name": "target",
                "type": "str",
                "optional": True
            }
        ],
        "returns": "all_ok, missing_dependencies, summary",
    },
    "tool_meta_audit": {
        "category": "health",
        "description": "Audit tool.meta.json coverage and minimal schema across tool folders",
        "args": [],
        "returns": "scanned_tools, missing_meta_count, invalid_meta_count, all_ok, summary",
    },
    "dns_lookup": {
        "category": "networking",
        "description": "Resolve a hostname to A/AAAA addresses and aliases",
        "args": [
            {"name": "host", "type": "str"},
            {"name": "port", "type": "int", "optional": True, "default": 443}
        ],
        "returns": "resolved addresses, aliases, canonical_name, summary",
    },
    "reverse_dns_lookup": {
        "category": "networking",
        "description": "Resolve an IP address to PTR/hostname info",
        "args": [
            {"name": "ip", "type": "str"}
        ],
        "returns": "hostname, aliases, addresses, summary",
    },
    "http_head_probe": {
        "category": "networking",
        "description": "Issue HTTP HEAD request and return status/headers timing",
        "args": [
            {"name": "url", "type": "str"},
            {"name": "timeout_seconds", "type": "int", "optional": True, "default": 8}
        ],
        "returns": "status_code, headers, elapsed_ms, summary",
    },
    "tls_cert_probe": {
        "category": "networking",
        "description": "Fetch TLS certificate metadata for a host:port",
        "args": [
            {"name": "host", "type": "str"},
            {"name": "port", "type": "int", "optional": True, "default": 443},
            {"name": "timeout_seconds", "type": "int", "optional": True, "default": 8}
        ],
        "returns": "subject, issuer, not_before, not_after, serial_number, summary",
    },
    "network_interface_info": {
        "category": "networking",
        "description": "List local hostname and interface address candidates",
        "args": [],
        "returns": "hostname, fqdn, addresses, summary",
    },
    "rpg_adventure_builder": {
        "category": "game_systems",
        "description": "Generate a full interactive CLI RPG adventure game into mini-codex/aish_tests with save/load and rich terminal UX",
        "args": [{"name": "target_dir", "type": "str", "optional": True}],
        "returns": "success, files_created, game_root, summary, elapsed_ms",
    },
    "directory_structure_generator": {
        "category": "execution",
        "description": "Create nested directory structures from JSON spec",
        "args": [{"name": "spec_json", "type": "str"}],
        "returns": "success, dirs_created, files_created, summary, elapsed_ms",
    },
    "python_module_generator": {
        "category": "execution",
        "description": "Generate Python module code from JSON specifications",
        "args": [{"name": "module_spec_json", "type": "str"}],
        "returns": "success, files_written, module_paths, summary, elapsed_ms",
    },
    "rpg_game_builder": {
        "category": "game_systems",
        "description": "Generate complete CLI RPG adventure game with all systems",
        "args": [],
        "returns": "success, files_created, game_root, summary, elapsed_ms",
    },
    "character_system_generator": {
        "category": "game_systems",
        "description": "Generate player character system with stats and progression",
        "args": [],
        "returns": "success, modules_created, classes_defined, summary, elapsed_ms",
    },
    "monster_system_generator": {
        "category": "game_systems",
        "description": "Generate monster definitions with varied types and loot",
        "args": [],
        "returns": "success, monsters_defined, monster_count, summary, elapsed_ms",
    },
    "combat_system_generator": {
        "category": "game_systems",
        "description": "Generate turn-based combat mechanics and balancing",
        "args": [],
        "returns": "success, modules_created, combat_functions, summary, elapsed_ms",
    },
    "ui_effects_generator": {
        "category": "game_systems",
        "description": "Generate terminal UI animations, loading bars, and big text",
        "args": [],
        "returns": "success, modules_created, effects_count, summary, elapsed_ms",
    },
    "shop_system_generator": {
        "category": "game_systems",
        "description": "Generate shops, traders, and rare item encounters",
        "args": [],
        "returns": "success, modules_created, shop_types, summary, elapsed_ms",
    },
    "saveload_system_generator": {
        "category": "game_systems",
        "description": "Generate game save/load and persistence mechanics",
        "args": [],
        "returns": "success, modules_created, functions_defined, summary, elapsed_ms",
    },
    "rest_system_generator": {
        "category": "game_systems",
        "description": "Generate rest locations and recovery mechanics",
        "args": [],
        "returns": "success, modules_created, rest_locations, summary, elapsed_ms",
    },
    "game_orchestrator": {
        "category": "game_systems",
        "description": "Orchestrate all game tools and build complete playable RPG",
        "args": [],
        "returns": "success, tools_executed, game_ready, summary, elapsed_ms",
    },
    "character_name_input": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_stat_strength_init": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_stat_defense_init": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_stat_wisdom_init": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_hp_calculator": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_level_initializer": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_experience_initializer": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_gold_initializer": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_damage_formula": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_damage_reducer_by_defense": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_heal_limiter": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_experience_accumulator": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_level_threshold_calculator": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_effective_levelup_check": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_level_incrementer": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_hp_growth_on_level": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_stat_growth_on_level": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_experience_reset_on_level": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_state_serializer": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_is_alive_checker": {
        "category": "game_systems",
        "description": "V2 Character system tool - atomic operation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "v2_branch_probe_tool": {
        "category": "game_systems",
        "description": "V2 branch probe tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_seed_roll": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_seed_normalizer": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_type_weapon_selector": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_type_armor_selector": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_type_alchemy_selector": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_type_relic_selector": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_type_black_market_selector": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_type_traveling_cart_selector": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_type_shrine_vendor_selector": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_type_arcane_bazaar_selector": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_inventory_slot_count_roll": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_inventory_slot_fill_policy": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_item_pool_common_load": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_item_pool_uncommon_load": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_item_pool_rare_load": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_item_pool_legendary_load": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_item_filter_by_level": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_item_filter_by_biome": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_item_filter_by_reputation": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_item_rarity_roll": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_item_price_base_calc": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_item_price_variance_roll": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_item_price_tax_apply": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_item_price_discount_apply": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_item_price_finalizer": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_vendor_mood_roll": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_vendor_greed_roll": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_vendor_kindness_roll": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_vendor_restock_timer_roll": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_vendor_restock_apply": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_rare_trader_spawn_roll": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_rare_trader_catalog_load": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_rare_trader_offer_limit_roll": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_rare_trader_offer_generate": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_rare_trader_departure_roll": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_player_affordability_check": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_player_inventory_capacity_check": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_species_seed_roll": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_species_selector": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_tier_selector": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_base_hp_calc": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_base_attack_calc": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_base_defense_calc": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_stat_variance_roll": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_stat_apply_variance": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_element_roll": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_element_resistance_assign": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_element_weakness_assign": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_loot_table_common_load": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_loot_table_uncommon_load": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_loot_table_rare_load": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_loot_table_epic_load": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_loot_table_legendary_load": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_purchase_validation_gate": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_purchase_currency_deduct": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_purchase_item_grant": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_sellback_base_price_calc": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_sellback_condition_penalty": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_sellback_final_price_calc": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_transaction_receipt_build": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_ui_listing_formatter": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_supply_index_roll": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_demand_index_roll": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_supply_demand_price_adjust": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_region_markup_apply": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_faction_discount_apply": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_daily_special_roll": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "shop_daily_special_apply": {
        "category": "game_systems",
        "description": "V2 shop branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_turn_order_roll": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_initiative_base_calc": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_initiative_variance_roll": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_initiative_finalize": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_action_attack_validate": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_action_defend_validate": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_action_item_validate": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_action_run_validate": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_hit_chance_base_calc": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_hit_chance_modifier_apply": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_hit_roll": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_crit_chance_base_calc": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_crit_roll": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_damage_base_calc": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_damage_variance_roll": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_damage_armor_mitigation": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_damage_guard_mitigation": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_damage_finalize": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_status_effect_apply": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_status_effect_tick": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_status_effect_expire": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_victory_condition_check": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_defeat_condition_check": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_escape_chance_calc": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_escape_roll": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_location_selector": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_cost_base_calc": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_cost_reputation_modifier": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_cost_finalize": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_heal_base_calc": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_heal_bonus_apply": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_heal_finalize": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_buff_roll": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_debuff_cleanse_roll": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_time_advance_apply": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_slot_selector": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_path_resolver": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_schema_version_write": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_schema_version_read": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_checksum_build": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_checksum_verify": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_encrypt_toggle": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_serialize_character": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_serialize_inventory": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_deserialize_character": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_deserialize_inventory": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_title_ascii_render": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_loading_bar_frame_build": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_menu_option_render": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_status_panel_render": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_combat_log_line_render": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_shop_catalog_render": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_prompt_input_render": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_transition_frame_render": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_notification_render": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_spawn_biome_selector": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_spawn_time_selector": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_spawn_level_band_selector": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_spawn_pack_size_roll": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_spawn_elite_roll": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_spawn_boss_roll": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_loot_gold_base_calc": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_loot_gold_variance_roll": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_loot_gold_finalize": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_loot_drop_count_roll": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_loot_item_roll": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_xp_base_calc": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_xp_scaling_apply": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_xp_finalize": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_resistance_strength_roll": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_weakness_severity_roll": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_affix_selector": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_affix_power_roll": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_name_generator": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "monster_title_generator": {
        "category": "game_systems",
        "description": "V2 monster branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_stat_agility_init": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_stat_luck_init": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_stat_vitality_init": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_stat_intelligence_init": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_crit_chance_calc": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_dodge_chance_calc": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_block_chance_calc": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_attack_speed_calc": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_encumbrance_calc": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_move_speed_calc": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_level_curve_selector": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_level_curve_apply": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_skill_point_gain_calc": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_talent_unlock_check": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_respec_cost_calc": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_gold_gain_modifier_calc": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_xp_gain_modifier_calc": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_regen_rate_calc": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_status_resistance_calc": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "character_display_name_formatter": {
        "category": "game_systems",
        "description": "V2 character branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_target_selector": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_target_validation_gate": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_combo_counter_increment": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_combo_damage_bonus_calc": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_guard_state_set": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_guard_state_clear": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_stamina_cost_calc": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_stamina_apply": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_mana_cost_calc": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_mana_apply": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_action_queue_push": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_action_queue_pop": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_round_start_hooks": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_round_end_hooks": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_reward_xp_calc": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_reward_gold_calc": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_reward_loot_roll": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_reward_apply": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_battle_log_compact": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "combat_battle_log_verbose": {
        "category": "game_systems",
        "description": "V2 combat branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_event_selector": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_event_positive_roll": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_event_negative_roll": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_event_apply": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_food_bonus_calc": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_safety_rating_calc": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_encounter_interrupt_roll": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_recovery_time_calc": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_slot_metadata_write": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_slot_metadata_read": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_backup_create": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_backup_restore": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_conflict_detect": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_conflict_resolve": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_integrity_report_build": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_theme_selector": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_color_palette_roll": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_spacing_scale_calc": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_font_style_selector": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_cursor_mode_set": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_screen_clear_mode_set": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_input_hint_render": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_error_toast_render": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "game_v2_pipeline_orchestrator": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_layout_grid_selector": {
        "category": "game_systems",
        "description": "V2 UI branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_layout_card_renderer": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_layout_table_renderer": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_layout_stack_renderer": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_animation_tween_step": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_animation_stagger_delay_calc": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ui_animation_ease_selector": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_weather_penalty_roll": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_noise_interrupt_roll": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_guard_rotation_efficiency_calc": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "rest_party_morale_gain_calc": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_delta_snapshot_build": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_delta_snapshot_apply": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_slot_prune_policy": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "saveload_corruption_repair_attempt": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "game_v2_build_plan_compiler": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "game_v2_build_plan_validator": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "game_v2_build_step_scheduler": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "game_v2_build_step_executor": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "game_v2_build_result_aggregator": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "game_v2_quality_gate_checker": {
        "category": "game_systems",
        "description": "V2 branch leaf tool",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "game_blueprint_validator": {
        "category": "execution",
        "description": "Validate game blueprint structure against README spec - reads README and verifies all declared system folders exist and contain code",
        "args": [{"name": "target_path", "type": "str", "optional": True}],
        "returns": "success, summary, elapsed_ms",
    },
    "multi_game_engine_builder": {
        "category": "execution",
        "description": "Top-level config-driven multi-game engine builder",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "game_type_config_loader": {
        "category": "execution",
        "description": "Load and normalize game type config JSON for engine build",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "game_type_schema_validator": {
        "category": "execution",
        "description": "Validate game config against required schema and defaults",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "engine_mode_router": {
        "category": "execution",
        "description": "Route build plan by game_type mode and strategy",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "engine_directory_plan_compiler": {
        "category": "execution",
        "description": "Compile directory structure plan for target game mode",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "engine_module_plan_compiler": {
        "category": "execution",
        "description": "Compile Python module generation plan for target game mode",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "engine_directory_materializer": {
        "category": "execution",
        "description": "Materialize directory plan using directory_structure_generator",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "engine_module_materializer": {
        "category": "execution",
        "description": "Materialize module plan using python_module_generator",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "engine_quality_gate": {
        "category": "execution",
        "description": "Validate generated project quality and blueprint integrity",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "engine_report_aggregator": {
        "category": "execution",
        "description": "Aggregate build outputs into engine report and manifest",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "entity_system_generator": {
        "category": "execution",
        "description": "Generate generic entity system for any game type",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "vendor_system_generator": {
        "category": "execution",
        "description": "Generate generic vendor economy system for any game type",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "progression_system_generator": {
        "category": "execution",
        "description": "Generate generic progression model system for any game type",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "mission_system_generator": {
        "category": "execution",
        "description": "Generate mission and objective system modules",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "reputation_system_generator": {
        "category": "execution",
        "description": "Generate faction reputation system modules",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "economy_system_generator": {
        "category": "execution",
        "description": "Generate dynamic economy system modules",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "tool_usage_counter_refresh": {
        "category": "execution",
        "description": "Refresh tool usage counters and write AI + human JSON reports under ai_repo_tools/tool_usage",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "tool_usage_counter_show": {
        "category": "execution",
        "description": "Show current tool usage counters from ai_repo_tools/tool_usage",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "cyberpunk_sim_builder": {
        "category": "execution",
        "description": "Build cyberpunk simulation project using generic engine pipeline",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "roguelike_sim_builder": {
        "category": "execution",
        "description": "Build roguelike simulation project using generic engine pipeline",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "engine_profile_selector": {
        "category": "execution",
        "description": "Select reusable build profile for multi-project module generation",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "engine_template_catalog_loader": {
        "category": "execution",
        "description": "Load reusable module templates for many project types",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "engine_contract_generator": {
        "category": "execution",
        "description": "Generate cross-project interface contracts for modules",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "engine_dependency_map_builder": {
        "category": "execution",
        "description": "Build dependency map for generated modules across systems",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "engine_build_matrix_runner": {
        "category": "execution",
        "description": "Run build matrix across multiple game types and profiles",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "engine_project_manifest_writer": {
        "category": "execution",
        "description": "Write project manifest for generated multi-project builds",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "engine_case_packager": {
        "category": "execution",
        "description": "Package generated projects into reusable case bundles",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "engine_reusability_score": {
        "category": "execution",
        "description": "Score generated modules for cross-project reuse quality",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "taxonomy_probe_execution": {
        "category": "execution",
        "description": "Probe tool for six-level taxonomy routing",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "taxonomy_init_normalizer": {
        "category": "execution",
        "description": "Normalize taxonomy package __init__ wrappers by preserving leaf tool exports and resetting non-leaf packages.",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "taxonomy_probe_execution_status": {
        "category": "execution",
        "description": "Report taxonomy routing/probe status and basic package health checks.",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "cyberpunk_bar_sim_game_builder": {
        "category": "game_systems",
        "description": "Build a playable cyberpunk bar management simulation game from generated engine scaffold.",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "aish_tests_reorganizer": {
        "category": "execution",
        "description": "Rename and reorganize aish_tests game/test folders into gameplay-based categories with safe reference updates.",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "tool_library_report": {
        "category": "toolmaker",
        "description": "Generate a unified report of toolkit tools with descriptions, usage counts, and weighted complexity scoring.",
        "args": [
            {"name": "output_format", "type": "str", "optional": True, "default": "json"},
            {"name": "category_filter", "type": "str", "optional": True},
            {"name": "top_n", "type": "int", "optional": True, "default": 10},
        ],
        "returns": "success, summary, elapsed_ms",
    },
    "tool_dashboard_index": {
        "category": "toolmaker",
        "description": "Generate an HTML index page linking all tool_library_dashboard*.html files under ai_repo_tools/tool_usage",
        "args": [],
        "returns": "success, index_path, dashboard_count, summary, elapsed_ms",
    },
    "zoo_ticket_price_base_set": {
        "category": "game_systems",
        "description": "Set and validate adult ticket base price for a zoo day",
        "args": [],
        "returns": "success, price, validation_note, elapsed_ms",
    },
    "zoo_ticket_child_price_calc": {
        "category": "game_systems",
        "description": "Calculate child ticket price as discount from adult price",
        "args": [],
        "returns": "success, child_price, discount_pct, elapsed_ms",
    },
    "zoo_ticket_group_discount_apply": {
        "category": "game_systems",
        "description": "Apply group discount to a ticket subtotal based on group size",
        "args": [],
        "returns": "success, discounted_total, savings, discount_tier, elapsed_ms",
    },
    "zoo_ticket_season_pass_cost_calc": {
        "category": "game_systems",
        "description": "Calculate season pass cost from adult single ticket price and breakeven",
        "args": [],
        "returns": "success, season_pass_price, single_breakeven_visits, elapsed_ms",
    },
    "zoo_ticket_surge_pricing_apply": {
        "category": "game_systems",
        "description": "Apply surge pricing multiplier based on current zoo occupancy percent",
        "args": [],
        "returns": "success, final_price, surge_multiplier, tier, elapsed_ms",
    },
    "zoo_ticket_vip_price_calc": {
        "category": "game_systems",
        "description": "Calculate VIP experience ticket price including premium amenities",
        "args": [],
        "returns": "success, vip_price, premium_delta, elapsed_ms",
    },
    "zoo_visitor_type_selector": {
        "category": "game_systems",
        "description": "Select a visitor type (family/solo/group/school) by weighted roll",
        "args": [],
        "returns": "success, visitor_type, group_size, budget_tier, elapsed_ms",
    },
    "zoo_visitor_happiness_base_calc": {
        "category": "game_systems",
        "description": "Calculate visitor base happiness from time in zoo and exhibits visited",
        "args": [],
        "returns": "success, happiness, base_score, modifier, elapsed_ms",
    },
    "zoo_visitor_happiness_animal_bonus": {
        "category": "game_systems",
        "description": "Apply happiness bonus for watching active/feeding animals",
        "args": [],
        "returns": "success, bonus, animal_name, behavior_state, elapsed_ms",
    },
    "zoo_visitor_happiness_crowding_penalty": {
        "category": "game_systems",
        "description": "Apply happiness penalty when exhibit is over viewing capacity",
        "args": [],
        "returns": "success, penalty, crowding_ratio, tier, elapsed_ms",
    },
    "zoo_visitor_hunger_tick": {
        "category": "game_systems",
        "description": "Apply hunger increase to a visitor per hour in zoo",
        "args": [],
        "returns": "success, hunger_level, fed_flag, elapsed_ms",
    },
    "zoo_visitor_thirst_tick": {
        "category": "game_systems",
        "description": "Apply thirst increase to a visitor per hour based on weather",
        "args": [],
        "returns": "success, thirst_level, weather_modifier, elapsed_ms",
    },
    "zoo_visitor_budget_selector": {
        "category": "game_systems",
        "description": "Select visitor spending budget tier (low/mid/high/whale)",
        "args": [],
        "returns": "success, budget_tier, daily_spend_cap, elapsed_ms",
    },
    "zoo_visitor_review_score_calc": {
        "category": "game_systems",
        "description": "Calculate visitor exit survey review score from happiness and spend",
        "args": [],
        "returns": "success, review_score, stars, verdict, elapsed_ms",
    },
    "zoo_animal_species_selector": {
        "category": "game_systems",
        "description": "Select an animal species from the zoo species catalogue by biome and rarity",
        "args": [],
        "returns": "success, species, biome, rarity, danger_level, elapsed_ms",
    },
    "zoo_animal_purchase_cost_calc": {
        "category": "game_systems",
        "description": "Calculate purchase cost for an animal species based on rarity",
        "args": [],
        "returns": "success, purchase_cost, rarity, negotiated_price, elapsed_ms",
    },
    "zoo_animal_upkeep_cost_calc": {
        "category": "game_systems",
        "description": "Calculate monthly upkeep cost for an animal species",
        "args": [],
        "returns": "success, monthly_upkeep, feed_cost, vet_cost, elapsed_ms",
    },
    "zoo_animal_popularity_score": {
        "category": "game_systems",
        "description": "Calculate visitor popularity score for an animal species",
        "args": [],
        "returns": "success, popularity, species, crowd_magnet_flag, elapsed_ms",
    },
    "zoo_animal_health_tick": {
        "category": "game_systems",
        "description": "Apply daily health decay to an animal based on care quality",
        "args": [],
        "returns": "success, health, decay_amount, status, elapsed_ms",
    },
    "zoo_animal_behavior_state_calc": {
        "category": "game_systems",
        "description": "Determine animal behavior state from health and enrichment scores",
        "args": [],
        "returns": "success, behavior_state, enrichment_score, visitor_bonus, elapsed_ms",
    },
    "zoo_animal_breeding_chance_roll": {
        "category": "game_systems",
        "description": "Roll breeding probability for an adult animal pair in an exhibit",
        "args": [],
        "returns": "success, bred, probability, offspring_species, elapsed_ms",
    },
    "zoo_animal_biome_match_check": {
        "category": "game_systems",
        "description": "Check if an animal species is compatible with an exhibit biome",
        "args": [],
        "returns": "success, compatible, biome, species, penalty_flag, elapsed_ms",
    },
    "zoo_exhibit_biome_selector": {
        "category": "game_systems",
        "description": "Select exhibit biome type (savanna/arctic/rainforest/ocean/reptile)",
        "args": [],
        "returns": "success, biome, climate, capacity_modifier, elapsed_ms",
    },
    "zoo_exhibit_size_validator": {
        "category": "game_systems",
        "description": "Validate exhibit grid size is sufficient for the animal count and species",
        "args": [],
        "returns": "success, valid, min_required, actual_size, deficit, elapsed_ms",
    },
    "zoo_exhibit_fencing_tier_check": {
        "category": "game_systems",
        "description": "Check if installed fence tier matches the maximum animal danger level",
        "args": [],
        "returns": "success, safe, fence_tier, danger_level, breach_risk, elapsed_ms",
    },
    "zoo_exhibit_decoration_score_calc": {
        "category": "game_systems",
        "description": "Calculate decoration enrichment score from flora and item count",
        "args": [],
        "returns": "success, decoration_score, item_count, flora_count, tier, elapsed_ms",
    },
    "zoo_exhibit_star_rating_calc": {
        "category": "game_systems",
        "description": "Calculate exhibit star rating from decoration, capacity and animal health",
        "args": [],
        "returns": "success, star_rating, dimension_scores, elapsed_ms",
    },
    "zoo_exhibit_viewing_capacity_calc": {
        "category": "game_systems",
        "description": "Calculate maximum simultaneous viewer spots for an exhibit footprint",
        "args": [],
        "returns": "success, viewer_capacity, footprint_tiles, path_edge_count, elapsed_ms",
    },
    "zoo_food_stall_type_selector": {
        "category": "game_systems",
        "description": "Select a food stall type (hotdog/icecream/restaurant/vending) by budget",
        "args": [],
        "returns": "success, stall_type, setup_cost, daily_capacity, elapsed_ms",
    },
    "zoo_food_stall_revenue_calc": {
        "category": "game_systems",
        "description": "Calculate daily revenue for a food stall based on visitor traffic",
        "args": [],
        "returns": "success, daily_revenue, sales_count, avg_spend, elapsed_ms",
    },
    "zoo_food_stall_queue_len_calc": {
        "category": "game_systems",
        "description": "Calculate queue length at a food stall given visitor density",
        "args": [],
        "returns": "success, queue_length, wait_time_min, overflow_flag, elapsed_ms",
    },
    "zoo_food_thirst_weather_modifier": {
        "category": "game_systems",
        "description": "Apply weather multiplier to visitor thirst rate for drink sales boost",
        "args": [],
        "returns": "success, modifier, weather, temp_celsius, thirst_rate, elapsed_ms",
    },
    "zoo_food_stock_depletion_check": {
        "category": "game_systems",
        "description": "Check and report whether a food stall has run out of stock",
        "args": [],
        "returns": "success, depleted, stock_remaining, restock_cost, elapsed_ms",
    },
    "zoo_staff_type_selector": {
        "category": "game_systems",
        "description": "Select staff member type (keeper/vet/janitor/guide/security)",
        "args": [],
        "returns": "success, staff_type, base_salary, skill_level, elapsed_ms",
    },
    "zoo_staff_morale_tick": {
        "category": "game_systems",
        "description": "Apply daily morale decay to a staff member based on workload",
        "args": [],
        "returns": "success, morale, decay, low_morale_flag, elapsed_ms",
    },
    "zoo_staff_salary_calc": {
        "category": "game_systems",
        "description": "Calculate monthly salary for a staff member at a given skill level",
        "args": [],
        "returns": "success, salary, base, bonus, skill_level, elapsed_ms",
    },
    "zoo_staff_skill_upgrade_cost_calc": {
        "category": "game_systems",
        "description": "Calculate training cost to upgrade staff member skill by one level",
        "args": [],
        "returns": "success, upgrade_cost, from_level, to_level, elapsed_ms",
    },
    "zoo_staff_fatigue_tick": {
        "category": "game_systems",
        "description": "Apply fatigue accumulation to a staff member per shift worked",
        "args": [],
        "returns": "success, fatigue, increment, exhausted_flag, elapsed_ms",
    },
    "zoo_finance_ticket_revenue_calc": {
        "category": "game_systems",
        "description": "Calculate daily ticket revenue from visitor count and ticket price",
        "args": [],
        "returns": "success, revenue, visitor_count, avg_ticket_price, elapsed_ms",
    },
    "zoo_finance_food_revenue_calc": {
        "category": "game_systems",
        "description": "Calculate daily food and beverage revenue from stall count and traffic",
        "args": [],
        "returns": "success, revenue, stall_count, avg_spend, elapsed_ms",
    },
    "zoo_finance_animal_upkeep_expense": {
        "category": "game_systems",
        "description": "Calculate total monthly animal upkeep expense for all zoo animals",
        "args": [],
        "returns": "success, total_expense, animal_count, avg_per_animal, elapsed_ms",
    },
    "zoo_finance_staff_salary_expense": {
        "category": "game_systems",
        "description": "Calculate total monthly staff salary payroll expense",
        "args": [],
        "returns": "success, total_payroll, staff_count, avg_salary, elapsed_ms",
    },
    "zoo_finance_pnl_summary_build": {
        "category": "game_systems",
        "description": "Build daily P and L summary from revenue and expense streams",
        "args": [],
        "returns": "success, revenue, expenses, net_pnl, profit_flag, elapsed_ms",
    },
    "zoo_finance_loan_repayment_calc": {
        "category": "game_systems",
        "description": "Calculate monthly loan repayment from principal, rate, and term",
        "args": [],
        "returns": "success, monthly_payment, principal, interest_portion, elapsed_ms",
    },
    "zoo_calendar_day_advance": {
        "category": "game_systems",
        "description": "Advance the game calendar by one day and return season and events",
        "args": [],
        "returns": "success, day, month, season, weekend_flag, elapsed_ms",
    },
    "zoo_event_season_selector": {
        "category": "game_systems",
        "description": "Select the current game season from day number",
        "args": [],
        "returns": "success, season, season_visitor_modifier, special_event, elapsed_ms",
    },
    "zoo_event_random_positive_roll": {
        "category": "game_systems",
        "description": "Roll a random positive zoo event such as viral moment or press visit",
        "args": [],
        "returns": "success, event_name, visitor_boost, revenue_boost, duration_days, elapsed_ms",
    },
    "zoo_event_random_negative_roll": {
        "category": "game_systems",
        "description": "Roll a random negative zoo event such as animal escape or storm",
        "args": [],
        "returns": "success, event_name, repair_cost, visitor_penalty, severity, elapsed_ms",
    },
    "zoo_reputation_star_rating_calc": {
        "category": "game_systems",
        "description": "Calculate overall zoo star rating from happiness and review scores",
        "args": [],
        "returns": "success, star_rating, components, tier_label, elapsed_ms",
    },
    "zoo_reputation_review_aggregate": {
        "category": "game_systems",
        "description": "Aggregate visitor exit reviews into summary metrics",
        "args": [],
        "returns": "success, avg_score, total_reviews, positive_pct, top_complaint, elapsed_ms",
    },
    "zoo_marketing_campaign_cost_calc": {
        "category": "game_systems",
        "description": "Calculate cost for a marketing campaign tier (flyer/radio/tv/viral)",
        "args": [],
        "returns": "success, campaign_cost, tier, reach_estimate, elapsed_ms",
    },
    "zoo_marketing_visitor_reach_calc": {
        "category": "game_systems",
        "description": "Calculate additional visitor arrivals from an active marketing campaign",
        "args": [],
        "returns": "success, extra_visitors, campaign_efficiency, roi, elapsed_ms",
    },
    "zoo_prestige_points_calc": {
        "category": "game_systems",
        "description": "Calculate prestige points earned from zoo metrics this month",
        "args": [],
        "returns": "success, prestige_points, star_bonus, conservation_bonus, elapsed_ms",
    },
    "zoo_unlock_check": {
        "category": "game_systems",
        "description": "Check if a zoo feature or animal is unlocked at current prestige level",
        "args": [],
        "returns": "success, unlocked, feature_name, required_prestige, elapsed_ms",
    },
    "zoo_expansion_cost_calc": {
        "category": "game_systems",
        "description": "Calculate land expansion cost based on current zoo size and direction",
        "args": [],
        "returns": "success, expansion_cost, tiles_added, new_size, elapsed_ms",
    },
    "zoo_tycoon_builder": {
        "category": "game_systems",
        "description": "Orchestrate generation of a full playable Zoo Tycoon Python game using all zoo atomic tools",
        "args": [],
        "returns": "success, game_dir, modules_written, systems, elapsed_ms",
    },
    "zoo_toolmaker_gen1": {
        "category": "execution",
        "description": "Recursive zoo meta-tool generation layer",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "zoo_toolmaker_gen2": {
        "category": "execution",
        "description": "Recursive zoo meta-tool generation layer",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "zoo_toolmaker_gen3": {
        "category": "execution",
        "description": "Recursive zoo meta-tool generation layer",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "zoo_toolmaker_gen4": {
        "category": "execution",
        "description": "Recursive zoo meta-tool generation layer",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "zoo_toolmaker_gen5": {
        "category": "execution",
        "description": "Recursive zoo meta-tool generation layer",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "zoo_toolmaker_gen6": {
        "category": "execution",
        "description": "Recursive zoo meta-tool generation layer",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "recursive_toolchain_gen1": {
        "category": "execution",
        "description": "Generation-1 recursive toolchain seed manifest generator",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "recursive_toolchain_gen2": {
        "category": "execution",
        "description": "Generation-2 recursive toolchain seed manifest generator",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "recursive_toolchain_gen3": {
        "category": "execution",
        "description": "Generation-3 recursive toolchain seed manifest generator",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "recursive_toolchain_gen4": {
        "category": "execution",
        "description": "Generation-4 recursive toolchain seed manifest generator",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "recursive_toolchain_gen5": {
        "category": "execution",
        "description": "Generation-5 recursive toolchain seed manifest generator",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "recursive_toolchain_gen6": {
        "category": "execution",
        "description": "Generation-6 recursive toolchain terminal manifest generator",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ai_app_generator_project_builder": {
        "category": "execution",
        "description": "Build a runnable AI app generator test project under aish_tests",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ai_app_intent_branch": {
        "category": "execution",
        "description": "AI app tree branch 1: parse prompt into structured intent",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ai_app_plan_branch": {
        "category": "execution",
        "description": "AI app tree branch 2: build project plan from intent",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ai_app_spec_branch": {
        "category": "execution",
        "description": "AI app tree branch 3: build strict generation spec contract",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ai_app_backend_branch": {
        "category": "execution",
        "description": "AI app tree branch 4: generate backend and db assets",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ai_app_frontend_branch": {
        "category": "execution",
        "description": "AI app tree branch 5: generate frontend assets wired to backend",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
    "ai_app_validation_branch": {
        "category": "execution",
        "description": "AI app tree branch 6: validate cross-layer consistency and completeness",
        "args": [],
        "returns": "success, summary, elapsed_ms",
    },
}


def _discover_tools_from_filesystem() -> None:
    """Auto-discover tool folders not explicitly listed in TOOL_REGISTRY.

    Two-pass discovery:
    Pass 1: shallow scan of tools/<category>/<tool>/command.py  (legacy/generated layout)
    Pass 2: deep taxonomy walk - finds tools at any nesting depth inside category dirs
    where the leaf folder contains command.py and leaf-name != parent-path segment names above.

    Optional per-tool metadata file: tool.meta.json
    {
      "description": "...",
      "args": [...],
      "returns": "..."
    }
    """

    tools_root = Path(__file__).resolve().parent

    def _register_tool(tool_name: str, category: str, command_dir: Path) -> None:
        if tool_name in TOOL_REGISTRY:
            return
        description = f"Auto-discovered tool '{tool_name}'"
        args: list = []
        returns = "success, summary"
        meta_path = command_dir / "tool.meta.json"
        if meta_path.is_file():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                if isinstance(meta, dict):
                    description = str(meta.get("description", description))
                    args = meta.get("args", args) if isinstance(meta.get("args", []), list) else args
                    returns = str(meta.get("returns", returns))
            except Exception:
                pass
        TOOL_REGISTRY[tool_name] = {
            "category": category,
            "description": description,
            "args": args,
            "returns": returns,
        }

    for category in TOOL_CATEGORIES.keys():
        category_dir = tools_root / category
        if not category_dir.is_dir():
            continue

        discovered: list = []

        # Pass 1: shallow (legacy generated layout tools/<category>/<tool>/command.py)
        for child in sorted(category_dir.iterdir(), key=lambda p: p.name):
            if not child.is_dir() or child.name.startswith("__"):
                continue
            if not (child / "command.py").is_file():
                continue
            tool_name = child.name
            discovered.append(tool_name)
            _register_tool(tool_name, category, child)

        # Pass 2: deep taxonomy walk — find command.py at any deeper level
        # A leaf is a dir whose name matches its own directory (last segment) and has command.py
        try:
            for cmd_file in sorted(category_dir.rglob("command.py")):
                leaf_dir = cmd_file.parent
                # Skip already-covered shallow paths (depth == 1 under category_dir)
                try:
                    rel = leaf_dir.relative_to(category_dir)
                except ValueError:
                    continue
                parts = rel.parts
                if len(parts) <= 1:
                    continue  # already handled in pass 1
                tool_name = leaf_dir.name
                if tool_name.startswith("__"):
                    continue
                if tool_name in discovered:
                    continue
                discovered.append(tool_name)
                _register_tool(tool_name, category, leaf_dir)
        except Exception:
            pass

        existing = TOOL_CATEGORIES[category].get("tools", [])
        merged = []
        seen: set = set()
        for name in existing + discovered:
            if name in seen:
                continue
            seen.add(name)
            merged.append(name)
        TOOL_CATEGORIES[category]["tools"] = merged


_discover_tools_from_filesystem()


def get_tools_for_category(category: str):
    """Return list of tool names for a given category."""
    return TOOL_CATEGORIES.get(category, {}).get("tools", [])


def get_category(tool_name: str):
    """Return the category name for a tool, or None."""
    entry = TOOL_REGISTRY.get(tool_name)
    return entry["category"] if entry else None
