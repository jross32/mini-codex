"""
Golden cases for validation bed v0.

Each case is a dict with:
  name   - human-readable identifier
  tool   - dispatcher tool name
  repo   - absolute path used as cwd (repo_path)
  args   - list of string args passed to the tool
  expect - dict of conditions to check against (exit_code, success, payload.X)

Condition values:
  scalar              -> exact equality
  {"gte": N}          -> actual >= N
  {"contains": s}     -> s in str(actual) or s in json.dumps(actual) for lists
  {"not_contains": s} -> s not in str/json result
  {"not_none": True}  -> actual is not None
  {"truthy": True}    -> bool(actual) is True
  {"is_none": True}   -> actual is None
"""
import json
from pathlib import Path

_VALIDATIONS_DIR = Path(__file__).parent
_MINI_CODEX_ROOT = _VALIDATIONS_DIR.parent.parent   # validations -> ai_repo_tools -> mini-codex
_WORKSPACE_ROOT = _MINI_CODEX_ROOT.parent


def get_cases():
    mc = str(_MINI_CODEX_ROOT)
    apar = str(_WORKSPACE_ROOT / "project_dump" / "apaR" / "apaR" / "backend")
    cog = str(_WORKSPACE_ROOT / "project_dump" / "cog" / "cog")

    return [
        # ─── ai_read ──────────────────────────────────────────────────────────
        {
            "name": "python_basic",
            "tool": "ai_read",
            "repo": mc,
            "args": ["agent/planner.py"],
            "expect": {
                "success": True,
                "payload.line_count": {"gte": 30},
                # planner.py defines many functions; functions list must be non-empty
                "payload.functions": {"not_none": True},
                "payload.preview": {"contains": "def"},
            },
        },
        {
            "name": "json_config",
            "tool": "ai_read",
            "repo": mc,
            "args": ["agent_logs/tool_observations_summary.json"],
            "expect": {
                "success": True,
                "payload.preview": {"contains": "tool_counts"},
            },
        },
        {
            "name": "missing_file",
            "tool": "ai_read",
            "repo": mc,
            "args": ["no_such_file.py"],
            "expect": {
                "success": False,
                "exit_code": 2,
            },
        },

        # ─── test_select ──────────────────────────────────────────────────────
        {
            # agent_loop.py imports state, planner, tool_runner, evaluator, memory
            # test_select must return non-empty recommendations for these imports
            "name": "recommend_imports",
            "tool": "test_select",
            "repo": mc,
            "args": [
                json.dumps(["agent/agent_loop.py"]),
                "agent/agent_loop.py",
            ],
            "expect": {
                "success": True,
                "payload.recommended_files": {"truthy": True},
            },
        },
        {
            # Anti-regression: top recommendation must NOT be an __init__.py
            # (was a planner bug; test_select should recommend implementation files)
            "name": "init_not_top_rec",
            "tool": "test_select",
            "repo": mc,
            "args": [
                json.dumps(["agent/agent_loop.py"]),
                "agent/agent_loop.py",
            ],
            "expect": {
                "success": True,
                "payload.recommended_files.0.file": {"not_contains": "__init__"},
            },
        },
        {
            # state.py imports only stdlib (dataclasses, datetime, typing)
            # test_select must not crash; may return empty recommendations
            "name": "stdlib_only_no_crash",
            "tool": "test_select",
            "repo": mc,
            "args": [
                json.dumps(["agent/state.py"]),
                "agent/state.py",
            ],
            "expect": {
                "success": True,
            },
        },

        # ─── artifact_read ────────────────────────────────────────────────────
        {
            # JSONL file -> artifact_type "unknown" -> fallback with preview
            "name": "observations_jsonl",
            "tool": "artifact_read",
            "repo": mc,
            "args": ["agent_logs/tool_observations.jsonl"],
            "expect": {
                "success": True,
                "payload.line_count": {"gte": 1},
                "payload.preview": {"not_none": True},
            },
        },
        {
            # JSON summary -> artifact_type "json" -> parsed with top_level_keys
            "name": "summary_json",
            "tool": "artifact_read",
            "repo": mc,
            "args": ["agent_logs/tool_observations_summary.json"],
            "expect": {
                "success": True,
                "payload.parse_status": "parsed",
                "payload.top_level_keys": {"contains": "tool_counts"},
            },
        },

        # ─── cmd_run ──────────────────────────────────────────────────────────
        {
            # apaR auth tests are known-good: 5 tests pass
            "name": "pytest_passing",
            "tool": "cmd_run",
            "repo": apar,
            "args": ["tests/test_auth.py"],
            "expect": {
                "success": True,
                "payload.passed_count": 5,
                "payload.returncode": 0,
            },
        },
        {
            # cog tests fail due to missing pyflakes dependency
            "name": "pytest_failing",
            "tool": "cmd_run",
            "repo": cog,
            "args": ["tests/"],
            "expect": {
                "success": False,
                "payload.failed_count": {"gte": 1},
            },
        },
        {
            # python mode: target file does not exist -> structured error
            "name": "python_not_found",
            "tool": "cmd_run",
            "repo": mc,
            "args": ["nonexistent_script.py"],
            "expect": {
                "success": False,
                "exit_code": 2,
                "payload.error": "file_not_found",
            },
        },

        # ─── env_check ────────────────────────────────────────────────────────
        {
            # cog has pyflakes, requests, Flask-WTF in requirements.txt but
            # none of them are installed in the project venv → missing dep signal
            "name": "missing_dep_detected",
            "tool": "env_check",
            "repo": cog,
            "args": [],
            "expect": {
                "exit_code": 1,
                "success": False,
                "payload.parse_status": "parsed",
                "payload.missing_dependencies": {"contains": "pyflakes"},
            },
        },
        {
            # mini-codex has no requirements.txt / pyproject.toml → not_found path
            "name": "no_dep_file",
            "tool": "env_check",
            "repo": mc,
            "args": [],
            "expect": {
                "exit_code": 2,
                "success": False,
                "payload.parse_status": "not_found",
                "payload.source_file": {"is_none": True},
            },
        },

        # ─── fast analysis/process ────────────────────────────────────────────
        {
            "name": "fast_analyze_basic",
            "tool": "fast_analyze",
            "repo": mc,
            "args": ["5000"],
            "expect": {
                "success": True,
                "exit_code": 0,
                "payload.file_count": {"gte": 20},
                "payload.top_extensions": {"truthy": True},
            },
        },
        {
            "name": "fast_process_basic",
            "tool": "fast_process",
            "repo": mc,
            "args": ["5000"],
            "expect": {
                "success": True,
                "exit_code": 0,
                "payload.next_actions": {"truthy": True},
                "payload.summary": {"contains": "Primary doc"},
            },
        },
        {
            "name": "fast_prepare_basic",
            "tool": "fast_prepare",
            "repo": mc,
            "args": ["5000"],
            "expect": {
                "success": True,
                "exit_code": 0,
                "payload.preparation_steps": {"truthy": True},
                "payload.confirmed_checks.all_passed": True,
            },
        },
        {
            "name": "fast_evaluate_basic",
            "tool": "fast_evaluate",
            "repo": mc,
            "args": ["5000"],
            "expect": {
                "success": True,
                "exit_code": 0,
                "payload.score": {"gte": 0},
                "payload.summary": {"contains": "Evaluation score"},
            },
        },
        {
            "name": "bench_compare_basic",
            "tool": "bench_compare",
            "repo": mc,
            "args": ["5000", "4", "0"],
            "expect": {
                "success": True,
                "exit_code": 0,
                "payload.benchmark_mode": "legacy_vs_fast_process",
                "payload.gain.mean.multiplier": {"gte": 0.8},
                "payload.summary": {"contains": "fast_process mean gain"},
            },
        },
        {
            "name": "agent_audit_basic",
            "tool": "agent_audit",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.health_score": {"gte": 0},
                "payload.recommendations": {"truthy": True},
            },
        },
        {
            "name": "agent_improver_basic",
            "tool": "agent_improver",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.applied_count": {"gte": 0},
                "payload.summary": {"not_none": True},
            },
        },

        # ─── integration sentinel ────────────────────────────────────────────
        {
            # Small sequence-level sentinel: verify inspect/run-goal path reaches
            # repo_map -> ai_read -> test_select -> cmd_run without loop collapse.
            "name": "inspect_run_progression",
            "tool": "integration",
            "mode": "integration",
            "repo": apar,
            "integration": {
                "goal": "inspect code and run tests",
                "max_steps": 12,
                "memory_file": "agent_logs/validation_integration.log",
            },
            "expect": {
                "success": True,
                "payload.stage_order_ok": True,
                "payload.cmd_run_seen": True,
                "payload.cmd_run_after_test_select": True,
                "payload.no_loop_collapse": True,
                "payload.cmd_run_count": 1,
            },
        },
        {
            "name": "repo_map_basic",
            "tool": "repo_map",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
            },
        },
        {
            "name": "repo_health_check_basic",
            "tool": "repo_health_check",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "dep_readiness_check_basic",
            "tool": "dep_readiness_check",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "tool_meta_audit_basic",
            "tool": "tool_meta_audit",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.scanned_tools": {"gte": 1},
                "payload.summary": {"contains": "tool_meta_audit scanned"},
            },
        },
        {
            "name": "dep_graph_basic",
            "tool": "dep_graph",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rpg_adventure_builder_basic",
            "tool": "rpg_adventure_builder",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "directory_structure_generator_basic",
            "tool": "directory_structure_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "python_module_generator_basic",
            "tool": "python_module_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rpg_game_builder_basic",
            "tool": "rpg_game_builder",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_system_generator_basic",
            "tool": "character_system_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_system_generator_basic",
            "tool": "monster_system_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_system_generator_basic",
            "tool": "combat_system_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_effects_generator_basic",
            "tool": "ui_effects_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_system_generator_basic",
            "tool": "shop_system_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_system_generator_basic",
            "tool": "saveload_system_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_system_generator_basic",
            "tool": "rest_system_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "game_orchestrator_basic",
            "tool": "game_orchestrator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_name_input_basic",
            "tool": "character_name_input",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_stat_strength_init_basic",
            "tool": "character_stat_strength_init",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_stat_defense_init_basic",
            "tool": "character_stat_defense_init",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_stat_wisdom_init_basic",
            "tool": "character_stat_wisdom_init",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_hp_calculator_basic",
            "tool": "character_hp_calculator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_level_initializer_basic",
            "tool": "character_level_initializer",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_experience_initializer_basic",
            "tool": "character_experience_initializer",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_gold_initializer_basic",
            "tool": "character_gold_initializer",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_damage_formula_basic",
            "tool": "character_damage_formula",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_damage_reducer_by_defense_basic",
            "tool": "character_damage_reducer_by_defense",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_heal_limiter_basic",
            "tool": "character_heal_limiter",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_experience_accumulator_basic",
            "tool": "character_experience_accumulator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_level_threshold_calculator_basic",
            "tool": "character_level_threshold_calculator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_effective_levelup_check_basic",
            "tool": "character_effective_levelup_check",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_level_incrementer_basic",
            "tool": "character_level_incrementer",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_hp_growth_on_level_basic",
            "tool": "character_hp_growth_on_level",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_stat_growth_on_level_basic",
            "tool": "character_stat_growth_on_level",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_experience_reset_on_level_basic",
            "tool": "character_experience_reset_on_level",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_state_serializer_basic",
            "tool": "character_state_serializer",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_is_alive_checker_basic",
            "tool": "character_is_alive_checker",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "v2_branch_probe_tool_basic",
            "tool": "v2_branch_probe_tool",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_seed_roll_basic",
            "tool": "shop_seed_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_seed_normalizer_basic",
            "tool": "shop_seed_normalizer",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_type_weapon_selector_basic",
            "tool": "shop_type_weapon_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_type_armor_selector_basic",
            "tool": "shop_type_armor_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_type_alchemy_selector_basic",
            "tool": "shop_type_alchemy_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_type_relic_selector_basic",
            "tool": "shop_type_relic_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_type_black_market_selector_basic",
            "tool": "shop_type_black_market_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_type_traveling_cart_selector_basic",
            "tool": "shop_type_traveling_cart_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_type_shrine_vendor_selector_basic",
            "tool": "shop_type_shrine_vendor_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_type_arcane_bazaar_selector_basic",
            "tool": "shop_type_arcane_bazaar_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_inventory_slot_count_roll_basic",
            "tool": "shop_inventory_slot_count_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_inventory_slot_fill_policy_basic",
            "tool": "shop_inventory_slot_fill_policy",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_item_pool_common_load_basic",
            "tool": "shop_item_pool_common_load",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_item_pool_uncommon_load_basic",
            "tool": "shop_item_pool_uncommon_load",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_item_pool_rare_load_basic",
            "tool": "shop_item_pool_rare_load",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_item_pool_legendary_load_basic",
            "tool": "shop_item_pool_legendary_load",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_item_filter_by_level_basic",
            "tool": "shop_item_filter_by_level",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_item_filter_by_biome_basic",
            "tool": "shop_item_filter_by_biome",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_item_filter_by_reputation_basic",
            "tool": "shop_item_filter_by_reputation",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_item_rarity_roll_basic",
            "tool": "shop_item_rarity_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_item_price_base_calc_basic",
            "tool": "shop_item_price_base_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_item_price_variance_roll_basic",
            "tool": "shop_item_price_variance_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_item_price_tax_apply_basic",
            "tool": "shop_item_price_tax_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_item_price_discount_apply_basic",
            "tool": "shop_item_price_discount_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_item_price_finalizer_basic",
            "tool": "shop_item_price_finalizer",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_vendor_mood_roll_basic",
            "tool": "shop_vendor_mood_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_vendor_greed_roll_basic",
            "tool": "shop_vendor_greed_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_vendor_kindness_roll_basic",
            "tool": "shop_vendor_kindness_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_vendor_restock_timer_roll_basic",
            "tool": "shop_vendor_restock_timer_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_vendor_restock_apply_basic",
            "tool": "shop_vendor_restock_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_rare_trader_spawn_roll_basic",
            "tool": "shop_rare_trader_spawn_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_rare_trader_catalog_load_basic",
            "tool": "shop_rare_trader_catalog_load",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_rare_trader_offer_limit_roll_basic",
            "tool": "shop_rare_trader_offer_limit_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_rare_trader_offer_generate_basic",
            "tool": "shop_rare_trader_offer_generate",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_rare_trader_departure_roll_basic",
            "tool": "shop_rare_trader_departure_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_player_affordability_check_basic",
            "tool": "shop_player_affordability_check",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_player_inventory_capacity_check_basic",
            "tool": "shop_player_inventory_capacity_check",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_species_seed_roll_basic",
            "tool": "monster_species_seed_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_species_selector_basic",
            "tool": "monster_species_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_tier_selector_basic",
            "tool": "monster_tier_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_base_hp_calc_basic",
            "tool": "monster_base_hp_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_base_attack_calc_basic",
            "tool": "monster_base_attack_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_base_defense_calc_basic",
            "tool": "monster_base_defense_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_stat_variance_roll_basic",
            "tool": "monster_stat_variance_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_stat_apply_variance_basic",
            "tool": "monster_stat_apply_variance",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_element_roll_basic",
            "tool": "monster_element_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_element_resistance_assign_basic",
            "tool": "monster_element_resistance_assign",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_element_weakness_assign_basic",
            "tool": "monster_element_weakness_assign",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_loot_table_common_load_basic",
            "tool": "monster_loot_table_common_load",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_loot_table_uncommon_load_basic",
            "tool": "monster_loot_table_uncommon_load",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_loot_table_rare_load_basic",
            "tool": "monster_loot_table_rare_load",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_loot_table_epic_load_basic",
            "tool": "monster_loot_table_epic_load",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_loot_table_legendary_load_basic",
            "tool": "monster_loot_table_legendary_load",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_purchase_validation_gate_basic",
            "tool": "shop_purchase_validation_gate",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_purchase_currency_deduct_basic",
            "tool": "shop_purchase_currency_deduct",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_purchase_item_grant_basic",
            "tool": "shop_purchase_item_grant",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_sellback_base_price_calc_basic",
            "tool": "shop_sellback_base_price_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_sellback_condition_penalty_basic",
            "tool": "shop_sellback_condition_penalty",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_sellback_final_price_calc_basic",
            "tool": "shop_sellback_final_price_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_transaction_receipt_build_basic",
            "tool": "shop_transaction_receipt_build",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_ui_listing_formatter_basic",
            "tool": "shop_ui_listing_formatter",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_supply_index_roll_basic",
            "tool": "shop_supply_index_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_demand_index_roll_basic",
            "tool": "shop_demand_index_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_supply_demand_price_adjust_basic",
            "tool": "shop_supply_demand_price_adjust",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_region_markup_apply_basic",
            "tool": "shop_region_markup_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_faction_discount_apply_basic",
            "tool": "shop_faction_discount_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_daily_special_roll_basic",
            "tool": "shop_daily_special_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "shop_daily_special_apply_basic",
            "tool": "shop_daily_special_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_turn_order_roll_basic",
            "tool": "combat_turn_order_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_initiative_base_calc_basic",
            "tool": "combat_initiative_base_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_initiative_variance_roll_basic",
            "tool": "combat_initiative_variance_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_initiative_finalize_basic",
            "tool": "combat_initiative_finalize",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_action_attack_validate_basic",
            "tool": "combat_action_attack_validate",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_action_defend_validate_basic",
            "tool": "combat_action_defend_validate",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_action_item_validate_basic",
            "tool": "combat_action_item_validate",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_action_run_validate_basic",
            "tool": "combat_action_run_validate",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_hit_chance_base_calc_basic",
            "tool": "combat_hit_chance_base_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_hit_chance_modifier_apply_basic",
            "tool": "combat_hit_chance_modifier_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_hit_roll_basic",
            "tool": "combat_hit_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_crit_chance_base_calc_basic",
            "tool": "combat_crit_chance_base_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_crit_roll_basic",
            "tool": "combat_crit_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_damage_base_calc_basic",
            "tool": "combat_damage_base_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_damage_variance_roll_basic",
            "tool": "combat_damage_variance_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_damage_armor_mitigation_basic",
            "tool": "combat_damage_armor_mitigation",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_damage_guard_mitigation_basic",
            "tool": "combat_damage_guard_mitigation",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_damage_finalize_basic",
            "tool": "combat_damage_finalize",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_status_effect_apply_basic",
            "tool": "combat_status_effect_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_status_effect_tick_basic",
            "tool": "combat_status_effect_tick",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_status_effect_expire_basic",
            "tool": "combat_status_effect_expire",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_victory_condition_check_basic",
            "tool": "combat_victory_condition_check",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_defeat_condition_check_basic",
            "tool": "combat_defeat_condition_check",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_escape_chance_calc_basic",
            "tool": "combat_escape_chance_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_escape_roll_basic",
            "tool": "combat_escape_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_location_selector_basic",
            "tool": "rest_location_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_cost_base_calc_basic",
            "tool": "rest_cost_base_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_cost_reputation_modifier_basic",
            "tool": "rest_cost_reputation_modifier",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_cost_finalize_basic",
            "tool": "rest_cost_finalize",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_heal_base_calc_basic",
            "tool": "rest_heal_base_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_heal_bonus_apply_basic",
            "tool": "rest_heal_bonus_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_heal_finalize_basic",
            "tool": "rest_heal_finalize",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_buff_roll_basic",
            "tool": "rest_buff_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_debuff_cleanse_roll_basic",
            "tool": "rest_debuff_cleanse_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_time_advance_apply_basic",
            "tool": "rest_time_advance_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_slot_selector_basic",
            "tool": "saveload_slot_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_path_resolver_basic",
            "tool": "saveload_path_resolver",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_schema_version_write_basic",
            "tool": "saveload_schema_version_write",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_schema_version_read_basic",
            "tool": "saveload_schema_version_read",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_checksum_build_basic",
            "tool": "saveload_checksum_build",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_checksum_verify_basic",
            "tool": "saveload_checksum_verify",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_encrypt_toggle_basic",
            "tool": "saveload_encrypt_toggle",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_serialize_character_basic",
            "tool": "saveload_serialize_character",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_serialize_inventory_basic",
            "tool": "saveload_serialize_inventory",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_deserialize_character_basic",
            "tool": "saveload_deserialize_character",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_deserialize_inventory_basic",
            "tool": "saveload_deserialize_inventory",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_title_ascii_render_basic",
            "tool": "ui_title_ascii_render",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_loading_bar_frame_build_basic",
            "tool": "ui_loading_bar_frame_build",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_menu_option_render_basic",
            "tool": "ui_menu_option_render",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_status_panel_render_basic",
            "tool": "ui_status_panel_render",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_combat_log_line_render_basic",
            "tool": "ui_combat_log_line_render",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_shop_catalog_render_basic",
            "tool": "ui_shop_catalog_render",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_prompt_input_render_basic",
            "tool": "ui_prompt_input_render",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_transition_frame_render_basic",
            "tool": "ui_transition_frame_render",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_notification_render_basic",
            "tool": "ui_notification_render",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_spawn_biome_selector_basic",
            "tool": "monster_spawn_biome_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_spawn_time_selector_basic",
            "tool": "monster_spawn_time_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_spawn_level_band_selector_basic",
            "tool": "monster_spawn_level_band_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_spawn_pack_size_roll_basic",
            "tool": "monster_spawn_pack_size_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_spawn_elite_roll_basic",
            "tool": "monster_spawn_elite_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_spawn_boss_roll_basic",
            "tool": "monster_spawn_boss_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_loot_gold_base_calc_basic",
            "tool": "monster_loot_gold_base_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_loot_gold_variance_roll_basic",
            "tool": "monster_loot_gold_variance_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_loot_gold_finalize_basic",
            "tool": "monster_loot_gold_finalize",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_loot_drop_count_roll_basic",
            "tool": "monster_loot_drop_count_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_loot_item_roll_basic",
            "tool": "monster_loot_item_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_xp_base_calc_basic",
            "tool": "monster_xp_base_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_xp_scaling_apply_basic",
            "tool": "monster_xp_scaling_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_xp_finalize_basic",
            "tool": "monster_xp_finalize",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_resistance_strength_roll_basic",
            "tool": "monster_resistance_strength_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_weakness_severity_roll_basic",
            "tool": "monster_weakness_severity_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_affix_selector_basic",
            "tool": "monster_affix_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_affix_power_roll_basic",
            "tool": "monster_affix_power_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_name_generator_basic",
            "tool": "monster_name_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "monster_title_generator_basic",
            "tool": "monster_title_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_stat_agility_init_basic",
            "tool": "character_stat_agility_init",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_stat_luck_init_basic",
            "tool": "character_stat_luck_init",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_stat_vitality_init_basic",
            "tool": "character_stat_vitality_init",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_stat_intelligence_init_basic",
            "tool": "character_stat_intelligence_init",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_crit_chance_calc_basic",
            "tool": "character_crit_chance_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_dodge_chance_calc_basic",
            "tool": "character_dodge_chance_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_block_chance_calc_basic",
            "tool": "character_block_chance_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_attack_speed_calc_basic",
            "tool": "character_attack_speed_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_encumbrance_calc_basic",
            "tool": "character_encumbrance_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_move_speed_calc_basic",
            "tool": "character_move_speed_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_level_curve_selector_basic",
            "tool": "character_level_curve_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_level_curve_apply_basic",
            "tool": "character_level_curve_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_skill_point_gain_calc_basic",
            "tool": "character_skill_point_gain_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_talent_unlock_check_basic",
            "tool": "character_talent_unlock_check",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_respec_cost_calc_basic",
            "tool": "character_respec_cost_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_gold_gain_modifier_calc_basic",
            "tool": "character_gold_gain_modifier_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_xp_gain_modifier_calc_basic",
            "tool": "character_xp_gain_modifier_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_regen_rate_calc_basic",
            "tool": "character_regen_rate_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_status_resistance_calc_basic",
            "tool": "character_status_resistance_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "character_display_name_formatter_basic",
            "tool": "character_display_name_formatter",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_target_selector_basic",
            "tool": "combat_target_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_target_validation_gate_basic",
            "tool": "combat_target_validation_gate",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_combo_counter_increment_basic",
            "tool": "combat_combo_counter_increment",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_combo_damage_bonus_calc_basic",
            "tool": "combat_combo_damage_bonus_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_guard_state_set_basic",
            "tool": "combat_guard_state_set",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_guard_state_clear_basic",
            "tool": "combat_guard_state_clear",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_stamina_cost_calc_basic",
            "tool": "combat_stamina_cost_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_stamina_apply_basic",
            "tool": "combat_stamina_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_mana_cost_calc_basic",
            "tool": "combat_mana_cost_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_mana_apply_basic",
            "tool": "combat_mana_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_action_queue_push_basic",
            "tool": "combat_action_queue_push",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_action_queue_pop_basic",
            "tool": "combat_action_queue_pop",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_round_start_hooks_basic",
            "tool": "combat_round_start_hooks",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_round_end_hooks_basic",
            "tool": "combat_round_end_hooks",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_reward_xp_calc_basic",
            "tool": "combat_reward_xp_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_reward_gold_calc_basic",
            "tool": "combat_reward_gold_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_reward_loot_roll_basic",
            "tool": "combat_reward_loot_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_reward_apply_basic",
            "tool": "combat_reward_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_battle_log_compact_basic",
            "tool": "combat_battle_log_compact",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "combat_battle_log_verbose_basic",
            "tool": "combat_battle_log_verbose",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_event_selector_basic",
            "tool": "rest_event_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_event_positive_roll_basic",
            "tool": "rest_event_positive_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_event_negative_roll_basic",
            "tool": "rest_event_negative_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_event_apply_basic",
            "tool": "rest_event_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_food_bonus_calc_basic",
            "tool": "rest_food_bonus_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_safety_rating_calc_basic",
            "tool": "rest_safety_rating_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_encounter_interrupt_roll_basic",
            "tool": "rest_encounter_interrupt_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_recovery_time_calc_basic",
            "tool": "rest_recovery_time_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_slot_metadata_write_basic",
            "tool": "saveload_slot_metadata_write",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_slot_metadata_read_basic",
            "tool": "saveload_slot_metadata_read",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_backup_create_basic",
            "tool": "saveload_backup_create",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_backup_restore_basic",
            "tool": "saveload_backup_restore",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_conflict_detect_basic",
            "tool": "saveload_conflict_detect",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_conflict_resolve_basic",
            "tool": "saveload_conflict_resolve",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_integrity_report_build_basic",
            "tool": "saveload_integrity_report_build",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_theme_selector_basic",
            "tool": "ui_theme_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_color_palette_roll_basic",
            "tool": "ui_color_palette_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_spacing_scale_calc_basic",
            "tool": "ui_spacing_scale_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_font_style_selector_basic",
            "tool": "ui_font_style_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_cursor_mode_set_basic",
            "tool": "ui_cursor_mode_set",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_screen_clear_mode_set_basic",
            "tool": "ui_screen_clear_mode_set",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_input_hint_render_basic",
            "tool": "ui_input_hint_render",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_error_toast_render_basic",
            "tool": "ui_error_toast_render",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "game_v2_pipeline_orchestrator_basic",
            "tool": "game_v2_pipeline_orchestrator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_layout_grid_selector_basic",
            "tool": "ui_layout_grid_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_layout_card_renderer_basic",
            "tool": "ui_layout_card_renderer",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_layout_table_renderer_basic",
            "tool": "ui_layout_table_renderer",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_layout_stack_renderer_basic",
            "tool": "ui_layout_stack_renderer",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_animation_tween_step_basic",
            "tool": "ui_animation_tween_step",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_animation_stagger_delay_calc_basic",
            "tool": "ui_animation_stagger_delay_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ui_animation_ease_selector_basic",
            "tool": "ui_animation_ease_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_weather_penalty_roll_basic",
            "tool": "rest_weather_penalty_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_noise_interrupt_roll_basic",
            "tool": "rest_noise_interrupt_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_guard_rotation_efficiency_calc_basic",
            "tool": "rest_guard_rotation_efficiency_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "rest_party_morale_gain_calc_basic",
            "tool": "rest_party_morale_gain_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_delta_snapshot_build_basic",
            "tool": "saveload_delta_snapshot_build",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_delta_snapshot_apply_basic",
            "tool": "saveload_delta_snapshot_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_slot_prune_policy_basic",
            "tool": "saveload_slot_prune_policy",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "saveload_corruption_repair_attempt_basic",
            "tool": "saveload_corruption_repair_attempt",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "game_v2_build_plan_compiler_basic",
            "tool": "game_v2_build_plan_compiler",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "game_v2_build_plan_validator_basic",
            "tool": "game_v2_build_plan_validator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "game_v2_build_step_scheduler_basic",
            "tool": "game_v2_build_step_scheduler",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "game_v2_build_step_executor_basic",
            "tool": "game_v2_build_step_executor",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "game_v2_build_result_aggregator_basic",
            "tool": "game_v2_build_result_aggregator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "game_v2_quality_gate_checker_basic",
            "tool": "game_v2_quality_gate_checker",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "game_blueprint_validator_basic",
            "tool": "game_blueprint_validator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "multi_game_engine_builder_basic",
            "tool": "multi_game_engine_builder",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "game_type_config_loader_basic",
            "tool": "game_type_config_loader",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "game_type_schema_validator_basic",
            "tool": "game_type_schema_validator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "engine_mode_router_basic",
            "tool": "engine_mode_router",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "engine_directory_plan_compiler_basic",
            "tool": "engine_directory_plan_compiler",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "engine_module_plan_compiler_basic",
            "tool": "engine_module_plan_compiler",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "engine_directory_materializer_basic",
            "tool": "engine_directory_materializer",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "engine_module_materializer_basic",
            "tool": "engine_module_materializer",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "engine_quality_gate_basic",
            "tool": "engine_quality_gate",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "engine_report_aggregator_basic",
            "tool": "engine_report_aggregator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "entity_system_generator_basic",
            "tool": "entity_system_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "vendor_system_generator_basic",
            "tool": "vendor_system_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "progression_system_generator_basic",
            "tool": "progression_system_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "mission_system_generator_basic",
            "tool": "mission_system_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "reputation_system_generator_basic",
            "tool": "reputation_system_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "economy_system_generator_basic",
            "tool": "economy_system_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "tool_usage_counter_refresh_basic",
            "tool": "tool_usage_counter_refresh",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "tool_usage_counter_show_basic",
            "tool": "tool_usage_counter_show",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "cyberpunk_sim_builder_basic",
            "tool": "cyberpunk_sim_builder",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "roguelike_sim_builder_basic",
            "tool": "roguelike_sim_builder",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "engine_profile_selector_basic",
            "tool": "engine_profile_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "engine_template_catalog_loader_basic",
            "tool": "engine_template_catalog_loader",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "engine_contract_generator_basic",
            "tool": "engine_contract_generator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "engine_dependency_map_builder_basic",
            "tool": "engine_dependency_map_builder",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "engine_build_matrix_runner_basic",
            "tool": "engine_build_matrix_runner",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "engine_project_manifest_writer_basic",
            "tool": "engine_project_manifest_writer",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "engine_case_packager_basic",
            "tool": "engine_case_packager",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "engine_reusability_score_basic",
            "tool": "engine_reusability_score",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "taxonomy_probe_execution_basic",
            "tool": "taxonomy_probe_execution",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "taxonomy_init_normalizer_basic",
            "tool": "taxonomy_init_normalizer",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "taxonomy_probe_execution_status_basic",
            "tool": "taxonomy_probe_execution_status",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "cyberpunk_bar_sim_game_builder_basic",
            "tool": "cyberpunk_bar_sim_game_builder",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "aish_tests_reorganizer_basic",
            "tool": "aish_tests_reorganizer",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "tool_audit_basic",
            "tool": "tool_audit",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.tools_found": {"gte": 400},
                "payload.summary": {"contains": "Audited"},
            },
        },
        {
            "name": "tool_audit_table_mode",
            "tool": "tool_audit",
            "repo": mc,
            "args": ["table", "8"],
            "expect": {
                "success": True,
                "payload.output_format": "table",
                "payload.cli_view": {"contains": "Top Priorities"},
            },
        },
        {
            "name": "tool_library_report_basic",
            "tool": "tool_library_report",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.broken_tool_count": {"gte": 1},
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "tool_library_report_table_mode",
            "tool": "tool_library_report",
            "repo": mc,
            "args": ["table"],
            "expect": {
                "success": True,
                "payload.output_format": "table",
                "payload.cli_view": {"contains": "Top Used"},
            },
        },
        {
            "name": "tool_library_report_filtered",
            "tool": "tool_library_report",
            "repo": mc,
            "args": ["json", "toolmaker", "6"],
            "expect": {
                "success": True,
                "payload.category_filter": "toolmaker",
                "payload.top_n": 6,
                "payload.dashboard_path": {"contains": "tool_library_dashboard_toolmaker_top6.html"},
            },
        },
        {
            "name": "tool_dashboard_index_basic",
            "tool": "tool_dashboard_index",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_ticket_price_base_set_basic",
            "tool": "zoo_ticket_price_base_set",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_ticket_child_price_calc_basic",
            "tool": "zoo_ticket_child_price_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_ticket_group_discount_apply_basic",
            "tool": "zoo_ticket_group_discount_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_ticket_season_pass_cost_calc_basic",
            "tool": "zoo_ticket_season_pass_cost_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_ticket_surge_pricing_apply_basic",
            "tool": "zoo_ticket_surge_pricing_apply",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_ticket_vip_price_calc_basic",
            "tool": "zoo_ticket_vip_price_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_visitor_type_selector_basic",
            "tool": "zoo_visitor_type_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_visitor_happiness_base_calc_basic",
            "tool": "zoo_visitor_happiness_base_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_visitor_happiness_animal_bonus_basic",
            "tool": "zoo_visitor_happiness_animal_bonus",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_visitor_happiness_crowding_penalty_basic",
            "tool": "zoo_visitor_happiness_crowding_penalty",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_visitor_hunger_tick_basic",
            "tool": "zoo_visitor_hunger_tick",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_visitor_thirst_tick_basic",
            "tool": "zoo_visitor_thirst_tick",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_visitor_budget_selector_basic",
            "tool": "zoo_visitor_budget_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_visitor_review_score_calc_basic",
            "tool": "zoo_visitor_review_score_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_animal_species_selector_basic",
            "tool": "zoo_animal_species_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_animal_purchase_cost_calc_basic",
            "tool": "zoo_animal_purchase_cost_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_animal_upkeep_cost_calc_basic",
            "tool": "zoo_animal_upkeep_cost_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_animal_popularity_score_basic",
            "tool": "zoo_animal_popularity_score",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_animal_health_tick_basic",
            "tool": "zoo_animal_health_tick",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_animal_behavior_state_calc_basic",
            "tool": "zoo_animal_behavior_state_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_animal_breeding_chance_roll_basic",
            "tool": "zoo_animal_breeding_chance_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_animal_biome_match_check_basic",
            "tool": "zoo_animal_biome_match_check",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_exhibit_biome_selector_basic",
            "tool": "zoo_exhibit_biome_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_exhibit_size_validator_basic",
            "tool": "zoo_exhibit_size_validator",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_exhibit_fencing_tier_check_basic",
            "tool": "zoo_exhibit_fencing_tier_check",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_exhibit_decoration_score_calc_basic",
            "tool": "zoo_exhibit_decoration_score_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_exhibit_star_rating_calc_basic",
            "tool": "zoo_exhibit_star_rating_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_exhibit_viewing_capacity_calc_basic",
            "tool": "zoo_exhibit_viewing_capacity_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_food_stall_type_selector_basic",
            "tool": "zoo_food_stall_type_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_food_stall_revenue_calc_basic",
            "tool": "zoo_food_stall_revenue_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_food_stall_queue_len_calc_basic",
            "tool": "zoo_food_stall_queue_len_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_food_thirst_weather_modifier_basic",
            "tool": "zoo_food_thirst_weather_modifier",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_food_stock_depletion_check_basic",
            "tool": "zoo_food_stock_depletion_check",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_staff_type_selector_basic",
            "tool": "zoo_staff_type_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_staff_morale_tick_basic",
            "tool": "zoo_staff_morale_tick",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_staff_salary_calc_basic",
            "tool": "zoo_staff_salary_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_staff_skill_upgrade_cost_calc_basic",
            "tool": "zoo_staff_skill_upgrade_cost_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_staff_fatigue_tick_basic",
            "tool": "zoo_staff_fatigue_tick",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_finance_ticket_revenue_calc_basic",
            "tool": "zoo_finance_ticket_revenue_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_finance_food_revenue_calc_basic",
            "tool": "zoo_finance_food_revenue_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_finance_animal_upkeep_expense_basic",
            "tool": "zoo_finance_animal_upkeep_expense",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_finance_staff_salary_expense_basic",
            "tool": "zoo_finance_staff_salary_expense",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_finance_pnl_summary_build_basic",
            "tool": "zoo_finance_pnl_summary_build",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_finance_loan_repayment_calc_basic",
            "tool": "zoo_finance_loan_repayment_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_calendar_day_advance_basic",
            "tool": "zoo_calendar_day_advance",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_event_season_selector_basic",
            "tool": "zoo_event_season_selector",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_event_random_positive_roll_basic",
            "tool": "zoo_event_random_positive_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_event_random_negative_roll_basic",
            "tool": "zoo_event_random_negative_roll",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_reputation_star_rating_calc_basic",
            "tool": "zoo_reputation_star_rating_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_reputation_review_aggregate_basic",
            "tool": "zoo_reputation_review_aggregate",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_marketing_campaign_cost_calc_basic",
            "tool": "zoo_marketing_campaign_cost_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_marketing_visitor_reach_calc_basic",
            "tool": "zoo_marketing_visitor_reach_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_prestige_points_calc_basic",
            "tool": "zoo_prestige_points_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_unlock_check_basic",
            "tool": "zoo_unlock_check",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_expansion_cost_calc_basic",
            "tool": "zoo_expansion_cost_calc",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_tycoon_builder_basic",
            "tool": "zoo_tycoon_builder",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_toolmaker_gen1_basic",
            "tool": "zoo_toolmaker_gen1",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_toolmaker_gen2_basic",
            "tool": "zoo_toolmaker_gen2",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_toolmaker_gen3_basic",
            "tool": "zoo_toolmaker_gen3",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_toolmaker_gen4_basic",
            "tool": "zoo_toolmaker_gen4",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_toolmaker_gen5_basic",
            "tool": "zoo_toolmaker_gen5",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "zoo_toolmaker_gen6_basic",
            "tool": "zoo_toolmaker_gen6",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "recursive_toolchain_gen1_basic",
            "tool": "recursive_toolchain_gen1",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "recursive_toolchain_gen2_basic",
            "tool": "recursive_toolchain_gen2",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "recursive_toolchain_gen3_basic",
            "tool": "recursive_toolchain_gen3",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "recursive_toolchain_gen4_basic",
            "tool": "recursive_toolchain_gen4",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "recursive_toolchain_gen5_basic",
            "tool": "recursive_toolchain_gen5",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "recursive_toolchain_gen6_basic",
            "tool": "recursive_toolchain_gen6",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ai_app_generator_project_builder_basic",
            "tool": "ai_app_generator_project_builder",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ai_app_intent_branch_basic",
            "tool": "ai_app_intent_branch",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ai_app_plan_branch_basic",
            "tool": "ai_app_plan_branch",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ai_app_spec_branch_basic",
            "tool": "ai_app_spec_branch",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ai_app_backend_branch_basic",
            "tool": "ai_app_backend_branch",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ai_app_frontend_branch_basic",
            "tool": "ai_app_frontend_branch",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
        {
            "name": "ai_app_validation_branch_basic",
            "tool": "ai_app_validation_branch",
            "repo": mc,
            "args": [],
            "expect": {
                "success": True,
                "payload.summary": {"not_none": True},
            },
        },
    ]
