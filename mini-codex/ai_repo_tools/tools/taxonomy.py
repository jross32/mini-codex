"""Shared 6-level taxonomy resolver for ai_repo_tools.

The taxonomy is the long-term folder standard:
    tools/<l1>/<l2>/<l3>/<l4>/<l5>/<l6>/<tool_name>/command.py

Registry categories remain stable for UX and discovery, while filesystem and
import paths are resolved through this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List


_BASE_SEGMENTS: Dict[str, List[str]] = {
    "discovery": ["repository_intelligence", "discovery", "scanning", "pattern_analysis", "signals"],
    "planning": ["workflow_design", "planning", "decision_support", "task_structuring", "routing"],
    "evaluation": ["quality_assurance", "evaluation", "measurement", "risk_analysis", "scoring"],
    "reading": ["content_extraction", "reading", "parsing", "structured_access", "summarization"],
    "execution": ["project_generation", "multi_project", "execution", "operations", "tool_functions"],
    "health": ["operational_health", "validation", "checks", "environment_review", "signals"],
    "networking": ["network_observability", "diagnostics", "connectivity", "transport_analysis", "probes"],
    "toolmaker": ["tool_ecosystem", "meta_operations", "creation", "improvement", "automation"],
    "game_systems": ["interactive_systems", "gameplay", "systems", "mechanics", "specializations"],
}

_EXECUTION_OVERRIDES: Dict[str, List[str]] = {
    "python_module_generator": ["project_generation", "multi_project", "module_generation", "python_modules", "generic_generators", "builders"],
    "directory_structure_generator": ["project_generation", "multi_project", "structure_generation", "filesystem_layouts", "directory_materializers", "builders"],
    "game_blueprint_validator": ["project_generation", "multi_project", "validation", "quality_gates", "blueprint_validation", "generated_projects"],
    "multi_game_engine_builder": ["project_generation", "multi_project", "engine_building", "orchestration", "top_level_builders", "config_driven"],
    "game_type_config_loader": ["project_generation", "multi_project", "configuration", "loading", "game_type_configs", "normalization"],
    "game_type_schema_validator": ["project_generation", "multi_project", "configuration", "validation", "schema_rules", "game_modes"],
    "engine_mode_router": ["project_generation", "multi_project", "engine_building", "routing", "mode_selection", "game_profiles"],
    "engine_directory_plan_compiler": ["project_generation", "multi_project", "planning", "filesystem_plans", "directory_layouts", "compilers"],
    "engine_module_plan_compiler": ["project_generation", "multi_project", "planning", "module_plans", "python_layouts", "compilers"],
    "engine_directory_materializer": ["project_generation", "multi_project", "materialization", "filesystem_execution", "directory_layouts", "writers"],
    "engine_module_materializer": ["project_generation", "multi_project", "materialization", "module_execution", "python_layouts", "writers"],
    "engine_quality_gate": ["project_generation", "multi_project", "validation", "quality_gates", "engine_outputs", "reviewers"],
    "engine_report_aggregator": ["project_generation", "multi_project", "reporting", "aggregation", "engine_outputs", "summaries"],
    "entity_system_generator": ["project_generation", "multi_project", "system_generation", "shared_systems", "entities", "generators"],
    "vendor_system_generator": ["project_generation", "multi_project", "system_generation", "shared_systems", "vendors", "generators"],
    "progression_system_generator": ["project_generation", "multi_project", "system_generation", "shared_systems", "progression", "generators"],
    "mission_system_generator": ["project_generation", "multi_project", "system_generation", "shared_systems", "missions", "generators"],
    "reputation_system_generator": ["project_generation", "multi_project", "system_generation", "shared_systems", "reputation", "generators"],
    "economy_system_generator": ["project_generation", "multi_project", "system_generation", "shared_systems", "economy", "generators"],
    "tool_usage_counter_refresh": ["project_generation", "multi_project", "observability", "usage_tracking", "counter_rebuilds", "refreshers"],
    "tool_usage_counter_show": ["project_generation", "multi_project", "observability", "usage_tracking", "counter_reports", "viewers"],
    "cyberpunk_sim_builder": ["project_generation", "multi_project", "engine_building", "mode_builders", "cyberpunk", "simulation_projects"],
    "roguelike_sim_builder": ["project_generation", "multi_project", "engine_building", "mode_builders", "roguelike", "simulation_projects"],
    "engine_profile_selector": ["project_generation", "multi_project", "configuration", "profiles", "build_profiles", "selectors"],
    "engine_template_catalog_loader": ["project_generation", "multi_project", "configuration", "templates", "module_templates", "catalogs"],
    "engine_contract_generator": ["project_generation", "multi_project", "contracts", "interfaces", "cross_project", "generators"],
    "engine_dependency_map_builder": ["project_generation", "multi_project", "analysis", "dependency_maps", "module_relationships", "builders"],
    "engine_build_matrix_runner": ["project_generation", "multi_project", "engine_building", "matrix_execution", "profile_coverage", "runners"],
    "engine_project_manifest_writer": ["project_generation", "multi_project", "reporting", "manifests", "project_metadata", "writers"],
    "engine_case_packager": ["project_generation", "multi_project", "packaging", "case_bundles", "reuse_artifacts", "packagers"],
    "engine_reusability_score": ["project_generation", "multi_project", "evaluation", "reuse_scoring", "cross_project_quality", "scorers"],
}


def _cluster_from_name(name: str) -> str:
    parts = [part for part in name.split("_") if part]
    if len(parts) >= 2:
        return f"{parts[0]}_{parts[1]}"
    if parts:
        return parts[0]
    return "general"


def taxonomy_segments(category: str, tool_name: str) -> List[str]:
    if category == "execution" and tool_name in _EXECUTION_OVERRIDES:
        return _EXECUTION_OVERRIDES[tool_name]

    base = list(_BASE_SEGMENTS.get(category, ["tool_library", "general", "operations", "taxonomy", "uncategorized"]))
    if len(base) < 5:
        base.extend(["general"] * (5 - len(base)))
    return base[:5] + [_cluster_from_name(tool_name)]


def taxonomy_import_module(category: str, tool_name: str) -> str:
    return "tools." + ".".join(taxonomy_segments(category, tool_name)) + f".{tool_name}.command"


def taxonomy_tool_dir(tools_root: Path, category: str, tool_name: str) -> Path:
    return tools_root.joinpath(*taxonomy_segments(category, tool_name), tool_name)
