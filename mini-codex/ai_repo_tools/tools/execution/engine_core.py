"""
Shared runtime for multi-game engine execution tools.

This module centralizes:
- config loading/validation/routing
- directory/module plan compilation + materialization
- quality gates + report aggregation
- persistent tool usage counters (AI + human JSON)
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from tools.execution.directory_structure_generator.command import run_directory_structure_generator
from tools.execution.game_blueprint_validator.command import run_game_blueprint_validator
from tools.execution.python_module_generator.command import run_python_module_generator


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ai_repo_root(repo_path: str) -> Path:
    return Path(repo_path) / "ai_repo_tools"


def _usage_dir(repo_path: str) -> Path:
    p = _ai_repo_root(repo_path) / "tool_usage"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _read_json(path: Path, default: Dict) -> Dict:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _increment_usage(repo_path: str, tool_name: str, summary: str = "") -> Dict:
    usage_path = _usage_dir(repo_path) / "usage_counter_ai.json"
    human_path = _usage_dir(repo_path) / "usage_counter_human.json"

    data = _read_json(
        usage_path,
        {
            "schema": "tool_usage.v1",
            "generated_at_utc": _now_utc(),
            "total_calls": 0,
            "tools": {},
        },
    )

    data["generated_at_utc"] = _now_utc()
    data["total_calls"] = int(data.get("total_calls", 0)) + 1

    tools = data.setdefault("tools", {})
    row = tools.setdefault(tool_name, {"count": 0, "last_called_utc": "", "last_summary": ""})
    row["count"] = int(row.get("count", 0)) + 1
    row["last_called_utc"] = _now_utc()
    if summary:
        row["last_summary"] = summary

    _write_json(usage_path, data)

    sorted_tools = sorted(
        (
            {"tool": name, "count": meta.get("count", 0), "last_called_utc": meta.get("last_called_utc", "")}
            for name, meta in tools.items()
        ),
        key=lambda x: (-x["count"], x["tool"]),
    )

    human = {
        "title": "Tool Usage Counter",
        "subtitle": "Human-readable summary of tool invocation counts",
        "generated_at_utc": data["generated_at_utc"],
        "total_calls": data["total_calls"],
        "top_tools": sorted_tools[:25],
        "notes": [
            "Counts are incremented whenever instrumented execution tools run.",
            "Use tool_usage_counter_refresh to rebuild counts from observation logs.",
        ],
    }
    _write_json(human_path, human)
    return data


def _refresh_usage_from_observations(repo_path: str) -> Dict:
    obs_path = _ai_repo_root(repo_path) / "agent_logs" / "tool_observations.jsonl"
    usage_path = _usage_dir(repo_path) / "usage_counter_ai.json"
    human_path = _usage_dir(repo_path) / "usage_counter_human.json"

    counts: Dict[str, int] = {}
    if obs_path.exists():
        for line in obs_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            tool = row.get("tool_name") or row.get("tool")
            if tool:
                counts[tool] = counts.get(tool, 0) + 1

    ai = {
        "schema": "tool_usage.v1",
        "generated_at_utc": _now_utc(),
        "source": str(obs_path.relative_to(Path(repo_path))) if obs_path.exists() else "missing",
        "total_calls": sum(counts.values()),
        "tools": {
            name: {
                "count": count,
                "last_called_utc": "",
                "last_summary": "rebuilt from observation log",
            }
            for name, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        },
    }
    _write_json(usage_path, ai)

    human = {
        "title": "Tool Usage Counter",
        "subtitle": "Rebuilt from observation log for AI and humans",
        "generated_at_utc": ai["generated_at_utc"],
        "total_calls": ai["total_calls"],
        "top_tools": [
            {"tool": name, "count": meta["count"]}
            for name, meta in list(ai["tools"].items())[:25]
        ],
        "source": ai["source"],
    }
    _write_json(human_path, human)
    return ai


def _default_config() -> Dict:
    return {
        "game_type": "cyberpunk",
        "project_name": "cyberpunk_bar_management_sim",
        "engine_version": "v1",
        "systems": ["core", "ui", "entities", "economy", "missions", "reputation", "vendor", "progression"],
    }


def _config_path(repo_path: str) -> Path:
    return _usage_dir(repo_path) / "engine_build_config.json"


def _load_config(repo_path: str) -> Dict:
    cfg_path = _config_path(repo_path)
    if not cfg_path.exists():
        cfg = _default_config()
        _write_json(cfg_path, cfg)
        return cfg
    return _read_json(cfg_path, _default_config())


def _validate_config(cfg: Dict) -> Tuple[bool, List[str]]:
    issues: List[str] = []
    if cfg.get("game_type") not in {"rpg", "cyberpunk", "roguelike"}:
        issues.append("game_type must be one of: rpg, cyberpunk, roguelike")
    if not cfg.get("project_name"):
        issues.append("project_name is required")
    if not isinstance(cfg.get("systems", []), list) or not cfg.get("systems"):
        issues.append("systems must be a non-empty list")
    return len(issues) == 0, issues


def _mode_profile(game_type: str) -> Dict:
    profiles = {
        "rpg": {
            "extra_dirs": ["systems/combat", "systems/loot", "systems/rest"],
            "theme": "fantasy",
        },
        "cyberpunk": {
            "extra_dirs": ["systems/hacking", "systems/factions", "systems/vendors"],
            "theme": "neon-noir",
        },
        "roguelike": {
            "extra_dirs": ["systems/dungeon", "systems/encounters", "systems/permadeath"],
            "theme": "procedural-survival",
        },
    }
    return profiles.get(game_type, profiles["cyberpunk"])


def _profile_catalog() -> Dict:
    return {
        "minimal": {"systems": ["core", "ui", "entities"], "complexity": 1},
        "simulation": {"systems": ["core", "ui", "entities", "economy", "missions", "reputation", "vendor"], "complexity": 2},
        "full_engine": {"systems": ["core", "ui", "entities", "economy", "missions", "reputation", "vendor", "progression"], "complexity": 3},
    }


def _template_catalog() -> Dict:
    return {
        "shared": ["core.engine", "entities.entity"],
        "cyberpunk": ["systems.hacking.hacking", "systems.factions.reputation", "systems.vendors.vendor"],
        "roguelike": ["systems.dungeon.dungeon", "systems.encounters.encounter", "systems.permadeath.life_cycle"],
        "rpg": ["systems.combat.combat", "systems.loot.loot", "systems.rest.recovery"],
    }


def _contract_spec(cfg: Dict) -> Dict:
    return {
        "engine": ["run", "load_mode"],
        "entity": ["get_stat"],
        "mode": [cfg["game_type"], "project_name", "systems"],
    }


def _dependency_map(cfg: Dict) -> Dict:
    game_type = cfg["game_type"]
    mapping = {
        "core.engine": ["entities.entity"],
        "entities.entity": [],
    }
    if game_type == "cyberpunk":
        mapping["systems.hacking.hacking"] = ["core.engine", "entities.entity"]
    elif game_type == "roguelike":
        mapping["systems.dungeon.dungeon"] = ["core.engine", "entities.entity"]
    else:
        mapping["systems.combat.combat"] = ["core.engine", "entities.entity"]
    return mapping


def _manifest_payload(cfg: Dict) -> Dict:
    profile = _mode_profile(cfg["game_type"])
    return {
        "project_name": cfg["project_name"],
        "game_type": cfg["game_type"],
        "engine_version": cfg.get("engine_version", "v1"),
        "theme": profile["theme"],
        "systems": cfg["systems"],
        "templates": _template_catalog().get(cfg["game_type"], []),
    }


def _case_bundle_payload(cfg: Dict) -> Dict:
    return {
        "case_name": f"{cfg['project_name']}_case_bundle",
        "project_name": cfg["project_name"],
        "game_type": cfg["game_type"],
        "artifacts": [
            f"aish_tests/multi_game_projects/{cfg['project_name']}",
            "ai_repo_tools/tool_usage/engine_build_last_result.json",
            "ai_repo_tools/tool_usage/engine_report.json",
        ],
    }


def _reusability_score_payload(cfg: Dict) -> Dict:
    shared_count = len(_template_catalog().get("shared", []))
    mode_count = len(_template_catalog().get(cfg["game_type"], []))
    total = shared_count + mode_count
    score = round((shared_count / total) * 100, 1) if total else 0.0
    return {
        "project_name": cfg["project_name"],
        "game_type": cfg["game_type"],
        "shared_templates": shared_count,
        "mode_templates": mode_count,
        "reusability_score": score,
    }


def _directory_spec(cfg: Dict) -> Dict:
    profile = _mode_profile(cfg["game_type"])
    base_dir = f"aish_tests/multi_game_projects/{cfg['project_name']}"

    dirs = [
        "core",
        "ui",
        "entities",
        "systems",
        "data",
        "config",
        "docs",
        "tests",
    ] + profile["extra_dirs"]

    files = {
        "README.md": (
            f"# {cfg['project_name']}\n\n"
            f"Game Type: {cfg['game_type']}\n"
            f"Theme: {profile['theme']}\n\n"
            "System folders:\n"
            "- core/\n"
            "- ui/\n"
            "- entities/\n"
            "- systems/\n"
        ),
        "core/__init__.py": "",
        "ui/__init__.py": "",
        "entities/__init__.py": "",
        "systems/__init__.py": "",
        "main.py": "from core.engine import Engine\n\nif __name__ == '__main__':\n    Engine().run()\n",
    }

    return {"base": base_dir, "dirs": dirs, "files": files}


def _base_modules(cfg: Dict) -> Dict:
    base_dir = f"aish_tests/multi_game_projects/{cfg['project_name']}"
    game_type = cfg["game_type"]

    modules = [
        {
            "path": "core/engine.py",
            "docstring": "Config-driven multi-game engine runtime",
            "imports": ["import json", "from pathlib import Path"],
            "classes": [
                {
                    "name": "Engine",
                    "docstring": "Main engine runtime for any game mode",
                    "attributes": [{"name": "mode"}, {"name": "tick"}],
                    "methods": [
                        {"name": "run", "code": "print(f'Running {self.mode} engine at tick {self.tick}')"},
                    ],
                }
            ],
            "functions": [
                {"name": "load_mode", "params": ["path"], "code": "return Path(path).read_text(encoding='utf-8')"}
            ],
        },
        {
            "path": "entities/entity.py",
            "docstring": "Generic entity model reused by all game types",
            "imports": ["from dataclasses import dataclass, field", "from typing import Dict, Any"],
            "classes": [
                {
                    "name": "Entity",
                    "docstring": "Universal entity",
                    "attributes": [{"name": "entity_id"}, {"name": "name"}, {"name": "stats"}],
                    "methods": [
                        {"name": "get_stat", "code": "return self.stats.get(key, 0)"},
                    ],
                }
            ],
            "functions": [],
        },
    ]

    if game_type == "cyberpunk":
        modules.append(
            {
                "path": "systems/hacking/hacking.py",
                "docstring": "Cyberpunk hacking subsystem",
                "imports": [],
                "classes": [{"name": "HackingSystem", "attributes": [{"name": "risk"}], "methods": [{"name": "attempt", "code": "return {'success': True, 'risk': self.risk}"}]}],
                "functions": [],
            }
        )
    elif game_type == "roguelike":
        modules.append(
            {
                "path": "systems/dungeon/dungeon.py",
                "docstring": "Roguelike dungeon subsystem",
                "imports": [],
                "classes": [{"name": "DungeonGenerator", "attributes": [{"name": "seed"}], "methods": [{"name": "generate", "code": "return {'rooms': 10, 'seed': self.seed}"}]}],
                "functions": [],
            }
        )
    else:
        modules.append(
            {
                "path": "systems/combat/combat.py",
                "docstring": "RPG combat subsystem",
                "imports": [],
                "classes": [{"name": "CombatSystem", "attributes": [{"name": "turn"}], "methods": [{"name": "next_turn", "code": "self.turn += 1\nreturn self.turn"}]}],
                "functions": [],
            }
        )

    return {"base_dir": base_dir, "modules": modules}


def _build_project(repo_path: str, cfg: Dict) -> Dict:
    base_dir = f"aish_tests/multi_game_projects/{cfg['project_name']}"
    manifest = _manifest_payload(cfg)
    contracts = _contract_spec(cfg)
    dependency_map = _dependency_map(cfg)
    case_bundle = _case_bundle_payload(cfg)
    reusability_score = _reusability_score_payload(cfg)

    _write_json(_usage_dir(repo_path) / "project_manifest.json", manifest)
    _write_json(_usage_dir(repo_path) / "engine_contracts.json", contracts)
    _write_json(_usage_dir(repo_path) / "engine_dependency_map.json", dependency_map)
    _write_json(_usage_dir(repo_path) / "case_bundle.json", case_bundle)
    _write_json(_usage_dir(repo_path) / "reusability_score.json", reusability_score)

    _, d_payload = run_directory_structure_generator(repo_path, spec_json=json.dumps(_directory_spec(cfg)))
    _, m_payload = run_python_module_generator(repo_path, module_spec_json=json.dumps(_base_modules(cfg)))
    _, q_payload = run_game_blueprint_validator(repo_path, target_path=str(Path(repo_path) / base_dir))
    report = {
        "game_type": cfg["game_type"],
        "project_name": cfg["project_name"],
        "project_root": base_dir,
        "manifest": manifest,
        "contracts": contracts,
        "dependency_map": dependency_map,
        "case_bundle": case_bundle,
        "reusability_score": reusability_score,
        "directory_result": d_payload,
        "module_result": m_payload,
        "quality_gate": q_payload,
    }
    report_path = _usage_dir(repo_path) / "engine_build_last_result.json"
    _write_json(report_path, report)
    return {
        "success": bool(d_payload.get("success", False) and m_payload.get("success", False)),
        "build": report,
        "result_path": str(report_path.relative_to(Path(repo_path))),
    }


def run_engine_tool(repo_path: str, tool_name: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()

    if tool_name == "tool_usage_counter_refresh":
        data = _refresh_usage_from_observations(repo_path)
        payload = {
            "success": True,
            "tool": tool_name,
            "summary": f"Rebuilt usage counters for {len(data.get('tools', {}))} tools",
            "usage_path": "ai_repo_tools/tool_usage/usage_counter_ai.json",
            "human_path": "ai_repo_tools/tool_usage/usage_counter_human.json",
            "total_calls": data.get("total_calls", 0),
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }
        _increment_usage(repo_path, tool_name, payload["summary"])
        return 0, payload

    if tool_name == "tool_usage_counter_show":
        data = _read_json(_usage_dir(repo_path) / "usage_counter_human.json", {})
        payload = {
            "success": True,
            "tool": tool_name,
            "summary": "Loaded tool usage counters",
            "report": data,
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }
        _increment_usage(repo_path, tool_name, payload["summary"])
        return 0, payload

    cfg = _load_config(repo_path)

    if tool_name == "game_type_config_loader":
        payload = {
            "success": True,
            "tool": tool_name,
            "config": cfg,
            "config_path": "ai_repo_tools/tool_usage/engine_build_config.json",
            "summary": f"Loaded config for {cfg['game_type']}",
        }
    elif tool_name == "game_type_schema_validator":
        ok, issues = _validate_config(cfg)
        payload = {
            "success": True,
            "tool": tool_name,
            "valid": ok,
            "issues": issues,
            "summary": "Config valid" if ok else f"Config invalid: {len(issues)} issues",
        }
    elif tool_name == "engine_mode_router":
        profile = _mode_profile(cfg["game_type"])
        payload = {
            "success": True,
            "tool": tool_name,
            "route": {"game_type": cfg["game_type"], "profile": profile},
            "summary": f"Routed to {cfg['game_type']} mode",
        }
    elif tool_name == "engine_profile_selector":
        catalog = _profile_catalog()
        selected = catalog["simulation"] if cfg["game_type"] in {"cyberpunk", "roguelike"} else catalog["full_engine"]
        payload = {
            "success": True,
            "tool": tool_name,
            "profiles": catalog,
            "selected_profile": selected,
            "summary": f"Selected profile for {cfg['game_type']}",
        }
    elif tool_name == "engine_template_catalog_loader":
        catalog = _template_catalog()
        payload = {
            "success": True,
            "tool": tool_name,
            "catalog": catalog,
            "active_templates": catalog.get("shared", []) + catalog.get(cfg["game_type"], []),
            "summary": f"Loaded template catalog for {cfg['game_type']}",
        }
    elif tool_name == "engine_contract_generator":
        contracts = _contract_spec(cfg)
        path = _usage_dir(repo_path) / "engine_contracts.json"
        _write_json(path, contracts)
        payload = {
            "success": True,
            "tool": tool_name,
            "contracts": contracts,
            "contracts_path": str(path.relative_to(Path(repo_path))),
            "summary": "Generated interface contracts",
        }
    elif tool_name == "engine_dependency_map_builder":
        dep_map = _dependency_map(cfg)
        path = _usage_dir(repo_path) / "engine_dependency_map.json"
        _write_json(path, dep_map)
        payload = {
            "success": True,
            "tool": tool_name,
            "dependency_map": dep_map,
            "dependency_map_path": str(path.relative_to(Path(repo_path))),
            "summary": "Built dependency map",
        }
    elif tool_name == "engine_directory_plan_compiler":
        spec = _directory_spec(cfg)
        _write_json(_usage_dir(repo_path) / "engine_directory_plan.json", spec)
        payload = {
            "success": True,
            "tool": tool_name,
            "directory_plan": spec,
            "plan_path": "ai_repo_tools/tool_usage/engine_directory_plan.json",
            "summary": f"Compiled directory plan for {cfg['project_name']}",
        }
    elif tool_name == "engine_module_plan_compiler":
        spec = _base_modules(cfg)
        _write_json(_usage_dir(repo_path) / "engine_module_plan.json", spec)
        payload = {
            "success": True,
            "tool": tool_name,
            "module_plan": spec,
            "plan_path": "ai_repo_tools/tool_usage/engine_module_plan.json",
            "summary": f"Compiled module plan for {cfg['project_name']}",
        }
    elif tool_name == "engine_directory_materializer":
        spec = _directory_spec(cfg)
        _, ds_payload = run_directory_structure_generator(repo_path, spec_json=json.dumps(spec))
        payload = {
            "success": bool(ds_payload.get("success", False)),
            "tool": tool_name,
            "result": ds_payload,
            "summary": ds_payload.get("summary", "Directory materialization complete"),
        }
    elif tool_name == "engine_module_materializer":
        spec = _base_modules(cfg)
        _, pm_payload = run_python_module_generator(repo_path, module_spec_json=json.dumps(spec))
        payload = {
            "success": bool(pm_payload.get("success", False)),
            "tool": tool_name,
            "result": pm_payload,
            "summary": pm_payload.get("summary", "Module materialization complete"),
        }
    elif tool_name in {
        "entity_system_generator",
        "vendor_system_generator",
        "progression_system_generator",
        "mission_system_generator",
        "reputation_system_generator",
        "economy_system_generator",
    }:
        # Specialized generators currently compile and materialize from shared module spec.
        spec = _base_modules(cfg)
        _, pm_payload = run_python_module_generator(repo_path, module_spec_json=json.dumps(spec))
        payload = {
            "success": bool(pm_payload.get("success", False)),
            "tool": tool_name,
            "result": pm_payload,
            "summary": f"{tool_name} generated base reusable modules",
        }
    elif tool_name == "engine_quality_gate":
        _, q_payload = run_game_blueprint_validator(
            repo_path,
            target_path=str(Path(repo_path) / f"aish_tests/multi_game_projects/{cfg['project_name']}"),
        )
        payload = {
            "success": True,
            "tool": tool_name,
            "quality": q_payload,
            "summary": "Quality gate executed",
        }
    elif tool_name == "engine_report_aggregator":
        usage = _read_json(_usage_dir(repo_path) / "usage_counter_ai.json", {})
        report = {
            "generated_at_utc": _now_utc(),
            "engine_config": cfg,
            "usage_totals": usage.get("total_calls", 0),
            "top_tools": [
                {"tool": name, "count": meta.get("count", 0)}
                for name, meta in list(usage.get("tools", {}).items())[:15]
            ],
        }
        report_path = _usage_dir(repo_path) / "engine_report.json"
        _write_json(report_path, report)
        payload = {
            "success": True,
            "tool": tool_name,
            "report_path": str(report_path.relative_to(Path(repo_path))),
            "summary": "Engine report aggregated",
            "report": report,
        }
    elif tool_name == "engine_project_manifest_writer":
        manifest = _manifest_payload(cfg)
        path = _usage_dir(repo_path) / "project_manifest.json"
        _write_json(path, manifest)
        payload = {
            "success": True,
            "tool": tool_name,
            "manifest": manifest,
            "manifest_path": str(path.relative_to(Path(repo_path))),
            "summary": "Project manifest written",
        }
    elif tool_name == "engine_case_packager":
        case_bundle = _case_bundle_payload(cfg)
        path = _usage_dir(repo_path) / "case_bundle.json"
        _write_json(path, case_bundle)
        payload = {
            "success": True,
            "tool": tool_name,
            "case_bundle": case_bundle,
            "case_bundle_path": str(path.relative_to(Path(repo_path))),
            "summary": "Case bundle packaged",
        }
    elif tool_name == "engine_reusability_score":
        score_payload = _reusability_score_payload(cfg)
        path = _usage_dir(repo_path) / "reusability_score.json"
        _write_json(path, score_payload)
        payload = {
            "success": True,
            "tool": tool_name,
            "score": score_payload,
            "score_path": str(path.relative_to(Path(repo_path))),
            "summary": "Calculated reusability score",
        }
    elif tool_name == "multi_game_engine_builder":
        ok, issues = _validate_config(cfg)
        if not ok:
            payload = {
                "success": False,
                "tool": tool_name,
                "issues": issues,
                "summary": "Build failed: invalid config",
            }
        else:
            built = _build_project(repo_path, cfg)
            payload = {
                "success": built["success"],
                "tool": tool_name,
                "build": built["build"],
                "result_path": built["result_path"],
                "summary": f"Built {cfg['game_type']} project at aish_tests/multi_game_projects/{cfg['project_name']}",
            }
    elif tool_name == "cyberpunk_sim_builder":
        cyber_cfg = dict(cfg)
        cyber_cfg["game_type"] = "cyberpunk"
        if not cyber_cfg.get("project_name") or cyber_cfg.get("project_name") == cfg.get("project_name"):
            cyber_cfg["project_name"] = "cyberpunk_bar_management_sim"
        built = _build_project(repo_path, cyber_cfg)
        payload = {
            "success": built["success"],
            "tool": tool_name,
            "build": built["build"],
            "result_path": built["result_path"],
            "summary": f"Built cyberpunk sim at aish_tests/multi_game_projects/{cyber_cfg['project_name']}",
        }
    elif tool_name == "roguelike_sim_builder":
        rogue_cfg = dict(cfg)
        rogue_cfg["game_type"] = "roguelike"
        if not rogue_cfg.get("project_name") or rogue_cfg.get("project_name") == cfg.get("project_name"):
            rogue_cfg["project_name"] = "roguelike_survival_sim"
        built = _build_project(repo_path, rogue_cfg)
        payload = {
            "success": built["success"],
            "tool": tool_name,
            "build": built["build"],
            "result_path": built["result_path"],
            "summary": f"Built roguelike sim at aish_tests/multi_game_projects/{rogue_cfg['project_name']}",
        }
    elif tool_name == "engine_build_matrix_runner":
        matrix = []
        for game_type, project_name in [
            ("rpg", "rpg_engine_case"),
            ("cyberpunk", "cyberpunk_bar_management_sim"),
            ("roguelike", "roguelike_survival_sim"),
        ]:
            matrix_cfg = dict(cfg)
            matrix_cfg["game_type"] = game_type
            matrix_cfg["project_name"] = project_name
            built = _build_project(repo_path, matrix_cfg)
            matrix.append({
                "game_type": game_type,
                "project_name": project_name,
                "success": built["success"],
                "result_path": built["result_path"],
            })
        path = _usage_dir(repo_path) / "build_matrix_results.json"
        _write_json(path, {"matrix": matrix, "generated_at_utc": _now_utc()})
        payload = {
            "success": all(row["success"] for row in matrix),
            "tool": tool_name,
            "matrix": matrix,
            "matrix_path": str(path.relative_to(Path(repo_path))),
            "summary": f"Ran build matrix for {len(matrix)} game types",
        }
    else:
        payload = {
            "success": False,
            "tool": tool_name,
            "summary": f"Unsupported engine tool: {tool_name}",
        }

    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    _increment_usage(repo_path, tool_name, payload.get("summary", ""))
    return (0 if payload.get("success", False) else 1), payload
