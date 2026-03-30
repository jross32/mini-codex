from typing import Optional, List, Dict, Any
from agent.state import AgentState
import re
import os
from agent.tool_policy import DEFAULT_SAFE_TOOLS, OPTIONAL_FAST_TOOLS
from agent.skill_loader import get_skill_tool_hints


def select_next_tool(state: AgentState) -> Optional[dict]:
    # Rule-based planner for V1.
    if state.status != "running":
        return None

    # Agent core self-upgrade loop (runs before toolkit loop)
    if state.agent_core_mode:
        return _select_agent_core_step(state)

    # Game build mode (small builders only)
    if state.game_builder_mode:
        return _select_game_builder_step(state)

    # Toolmaker improvement / creation loop (runs before standard file-read flow)
    if state.toolmaker_mode:
        return _select_toolmaker_step(state)

    # 1. If no repo map has been run yet, do it first.
    if "repo_map" not in state.tools_used:
        return {"tool": "repo_map", "args": []}

    # 1.4. Run any tool explicitly recommended by the active skills that hasn't
    # been used yet.  Only safe/known tools are returned by get_skill_tool_hints,
    # and repo_map is excluded because it already ran.
    for hint_tool in get_skill_tool_hints(state.artifacts):
        if hint_tool != "repo_map" and hint_tool not in state.tools_used:
            return {"tool": hint_tool, "args": []}

    # 1.5. For broad inspect/analyze goals, run default-safe fast_process once
    # before manual-style ai_read sequencing.
    if (
        "fast_process" in DEFAULT_SAFE_TOOLS
        and state.follow_up_allowed
        and "fast_process" not in state.tools_used
    ):
        return {"tool": "fast_process", "args": []}

    # 1.6. Intent-aware optional fast tools to improve planning quality and
    # reduce unnecessary deep file reads.
    intent = _goal_intent(state.goal)
    if "fast_prepare" in OPTIONAL_FAST_TOOLS and intent in {"execution", "readiness"} and "fast_prepare" not in state.tools_used:
        return {"tool": "fast_prepare", "args": []}
    if "fast_evaluate" in OPTIONAL_FAST_TOOLS and intent in {"quality", "review", "execution"} and "fast_evaluate" not in state.tools_used:
        return {"tool": "fast_evaluate", "args": []}
    if "fast_analyze" in OPTIONAL_FAST_TOOLS and intent in {"analysis", "review", "architecture"} and "fast_analyze" not in state.tools_used:
        return {"tool": "fast_analyze", "args": []}

    # 2. If repo mapped but no files read, read first known file with heuristic.
    if state.known_files and "ai_read" not in state.tools_used:
        planned_reads = state.artifacts.get("planned_reads", []) or []
        for candidate in planned_reads:
            if candidate in state.known_files and candidate not in state.read_files:
                return {"tool": "ai_read", "args": [candidate]}
            for known in state.known_files:
                if known in state.read_files:
                    continue
                if known.replace("\\", "/").endswith(candidate.replace("\\", "/")):
                    return {"tool": "ai_read", "args": [known]}
        target = select_initial_file(state.known_files)
        if target:
            return {"tool": "ai_read", "args": [target]}

    # 3. If ai_read done and follow-up allowed for broad goals, do follow-up read.
    # Tiny bounded extensions:
    # - allow one extra hop when last-read is BUILD_ORDER.md
    # - allow one additional hop when last-read is ai_repo_tools/main.py
    last_read_norm = (state.last_read_file or "").replace("\\", "/").lower()
    if last_read_norm.endswith("ai_repo_tools/main.py"):
        follow_up_limit = 4
    elif last_read_norm.endswith("build_order.md"):
        follow_up_limit = 3
    else:
        follow_up_limit = 2
    if "ai_read" in state.tools_used and state.follow_up_allowed and state.follow_up_reads_done < follow_up_limit and "test_select" not in state.tools_used:
        related = select_related_file(state)
        if related:
            return {"tool": "ai_read", "args": [related]}

    # 4. If ai_read done but no follow-up or follow-up done, use test_select
    if "ai_read" in state.tools_used and "test_select" not in state.tools_used:
        import json
        read_files_json = json.dumps(sorted(list(state.read_files)))
        last_read = state.last_read_file or ""
        return {"tool": "test_select", "args": [read_files_json, last_read]}

    # 4.4. After test_select, if the goal asks to run/test/verify, run env_check once
    # before cmd_run to detect missing dependencies early.
    if (
        "test_select" in state.tools_used
        and "env_check" not in state.tools_used
        and "cmd_run" not in state.tools_used
        and _goal_wants_execution(state.goal)
    ):
        return {"tool": "env_check", "args": []}

    # 4.5. After env_check (or if goal wants execution), use cmd_run once.
    if (
        "test_select" in state.tools_used
        and "env_check" in state.tools_used
        and "cmd_run" not in state.tools_used
        and _goal_wants_execution(state.goal)
    ):
        run_target = _extract_run_target(state)
        return {"tool": "cmd_run", "args": [run_target] if run_target else []}

    # 5. if no progress, stop.
    return None


def select_initial_file(known_files: List[str]) -> Optional[str]:

    """
    Intelligent initial file selection with priority ordering:
    
     Priority levels (in order):
     0. Orientation docs (AI_START_HERE.md / START_HERE.md / README.md),
         but only for very large tool-heavy repos
     1. Entry point files (app.py, main.py, __init__.py) - prefer app.py first
     2. Other non-agent .py files (excluding migration/tooling folders)
     3. Non-agent .md files
     4. Agent .py files
     5. Agent .md files
     6. Fallback to first file
    
    Additionally deprioritize migration/tooling folders when better options exist:
    - alembic/, migrations/, tests/, tools/, scripts/
    
    This helps repos like apaR read backend/app/__init__.py instead of backend/alembic/env.py
    """
    agent_prefixes = ("agent/", "ai_repo_tools/")
    tooling_prefixes = ("alembic/", "migrations/", "tests/", "tools/", "scripts/", ".egg-info/")
    
    def is_agent_file(path: str) -> bool:
        return path.startswith(agent_prefixes)
    
    def is_tooling_file(path: str) -> bool:
        """Check if file is in a migration/tooling folder."""
        for prefix in tooling_prefixes:
            if f"/{prefix}" in f"/{path}" or path.startswith(prefix):
                return True
        return False
    
    def get_filename(path: str) -> str:
        """Extract just the filename from a path."""
        return path.split("/")[-1]

    def is_large_tool_heavy_repo(files: List[str]) -> bool:
        """Heuristic gate to keep orientation-doc preference narrow and low-risk."""
        if len(files) < 2000:
            return False
        tool_py_count = sum(1 for f in files if f.startswith("ai_repo_tools/") and f.endswith(".py"))
        return tool_py_count >= 200

    # Tier 0: In large tool-heavy repos, prefer obvious orientation docs first.
    # This helps avoid reading arbitrary root utility scripts before repo guidance.
    if is_large_tool_heavy_repo(known_files):
        orientation_names = ("ai_start_here.md", "start_here.md", "readme.md")
        for doc_name in orientation_names:
            for candidate in known_files:
                if (
                    not is_agent_file(candidate)
                    and "/" not in candidate
                    and get_filename(candidate).lower() == doc_name
                ):
                    return candidate
    
    # Tier 1: Likely entry point files (app.py, main.py, __init__.py)
    # Prefer app.py first, then main.py, then __init__.py
    entry_point_names = ["app.py", "main.py", "__init__.py"]
    for entry_name in entry_point_names:
        for candidate in known_files:
            if (not is_agent_file(candidate) and 
                get_filename(candidate) == entry_name and
                not is_tooling_file(candidate)):
                return candidate
    
    # Tier 2: Other non-agent .py files (excluding tooling files)
    for candidate in known_files:
        if (not is_agent_file(candidate) and 
            candidate.endswith(".py") and
            not is_tooling_file(candidate)):
            return candidate
    
    # Tier 3: Non-agent .md files
    for candidate in known_files:
        if not is_agent_file(candidate) and candidate.endswith(".md"):
            return candidate
    
    # Tier 4: Agent .py files
    for candidate in known_files:
        if is_agent_file(candidate) and candidate.endswith(".py"):
            return candidate
    
    # Tier 5: Agent .md files
    for candidate in known_files:
        if is_agent_file(candidate) and candidate.endswith(".md"):
            return candidate
    
    # Tier 6: Fallback to first file
    if known_files:
        return known_files[0]
    
    return None



# ── toolmaker planner helpers ─────────────────────────────────────────────────


def _select_toolmaker_step(state: AgentState) -> Optional[dict]:
    """Route the friction-driven multi-iteration toolmaker loop."""
    goal = state.goal.lower()

    # ── Branch A: create / scaffold a brand-new tool ─────────────────────────
    if any(ph in goal for ph in ("create tool", "make tool", "new tool", "add tool", "scaffold tool")):
        if "toolmaker" not in state.tools_used:
            name = _extract_tool_name(state.goal)
            category = _extract_tool_category(state.goal)
            description = _extract_tool_description(state.goal)
            args: list = [name, category] if name else []
            if description:
                args.append(description)
            return {"tool": "toolmaker", "args": args}
        if "lint_check" not in state.tools_used:
            created = state.artifacts.get("toolmaker_created_file")
            return {"tool": "lint_check", "args": [created] if created else []}
        state.status = "complete"
        return None

    # ── Branch B: improve toolkit with friction + audit + iterative upgrades ──
    if not state.friction_step_done:
        return {"tool": "friction_summarizer", "args": []}

    if not state.toolmaker_audit_done:
        return {"tool": "tool_audit", "args": []}

    if not state.initial_audit_candidates:
        raw_candidates = state.artifacts.get("tool_audit_candidates_raw", []) or []
        friction_report = state.friction_report or state.artifacts.get("friction_report") or {}
        merged = _merge_candidates(raw_candidates, friction_report)
        state.initial_audit_candidates = merged
        state.artifacts["initial_audit_candidates"] = merged

    max_n = min(state.toolmaker_max_iterations, len(state.initial_audit_candidates))
    if max_n <= 0:
        if not state.toolmaker_reaudit_done:
            return {"tool": "tool_audit", "args": []}
        state.status = "complete"
        return None

    if state.toolmaker_iteration >= max_n:
        if not state.toolmaker_reaudit_done:
            return {"tool": "tool_audit", "args": []}
        state.status = "complete"
        return None

    candidate = state.initial_audit_candidates[state.toolmaker_iteration]
    target = candidate.get("tool") or state.toolmaker_target or state.artifacts.get("toolmaker_target")
    if not target:
        state.toolmaker_iteration += 1
        state.toolmaker_substep = "improve"
        return _select_toolmaker_step(state)

    state.toolmaker_target = target
    state.artifacts["toolmaker_target"] = target

    if state.toolmaker_substep not in {"improve", "lint", "validate"}:
        state.toolmaker_substep = "improve"

    if state.toolmaker_substep == "improve":
        spec = _derive_spec_from_gaps(target, candidate, state)
        if spec:
            args = [
                spec["name"],
                spec["category"],
                spec.get("description") or "Auto-generated helper tool.",
                spec.get("args_spec_json") or "[]",
                spec.get("returns_desc") or "success, summary, elapsed_ms",
            ]
            state.artifacts["toolmaker_active_action"] = "create"
            return {"tool": "toolmaker", "args": args}
        state.artifacts["toolmaker_active_action"] = "improve"
        return {"tool": "tool_improver", "args": [target]}

    if state.toolmaker_substep == "lint":
        target_path = state.artifacts.get("toolmaker_current_tool_path") or _get_tool_path(state.repo_path, target)
        return {"tool": "lint_check", "args": [target_path] if target_path else []}

    validation_target = _get_validation_cmd(state.repo_path, target)
    return {"tool": "cmd_run", "args": [validation_target] if validation_target else []}


def _merge_candidates(candidates: List[Dict[str, Any]], friction_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Merge baseline audit candidates with bounded friction weighting.
    priority_score = (baseline_gap) + bounded_friction_weight
    where bounded_friction_weight <= 3 to prevent friction domination.
    """
    friction_by_tool: Dict[str, float] = {}
    ranked = friction_report.get("ranked", []) if isinstance(friction_report, dict) else []
    for row in ranked:
        if not isinstance(row, dict):
            continue
        tool = row.get("tool")
        if not tool:
            continue
        count = float(row.get("count", 0) or 0)
        sev = float(row.get("severity_weight", 1) or 1)
        friction_by_tool[tool] = friction_by_tool.get(tool, 0.0) + (count * sev)

    merged: List[Dict[str, Any]] = []
    for c in candidates:
        if not isinstance(c, dict):
            continue
        tool = c.get("tool")
        if not tool:
            continue
        baseline = int(c.get("baseline_score", c.get("score", 0)) or 0)
        max_baseline = int(c.get("baseline_max_score", c.get("max_score", 5)) or 5)
        baseline_gap = max(0, max_baseline - baseline)
        friction_raw = friction_by_tool.get(tool, 0.0)
        friction_weight = min(3.0, friction_raw / 3.0)
        priority_score = round(baseline_gap + friction_weight, 3)

        item = dict(c)
        item["baseline_gap"] = baseline_gap
        item["friction_weight"] = round(friction_weight, 3)
        item["priority_score"] = priority_score
        merged.append(item)

    merged.sort(key=lambda x: (-x.get("priority_score", 0), x.get("tool", "")))
    return merged


def _derive_spec_from_gaps(tool_name: str, candidate: Dict[str, Any], state: AgentState) -> Optional[Dict[str, str]]:
    """Patch-first policy: only scaffold a new tool for clear missing-capability friction."""
    ranked = (state.friction_report or {}).get("ranked", []) if isinstance(state.friction_report, dict) else []
    has_missing_dep = any(
        isinstance(row, dict)
        and row.get("tool") == "cmd_run"
        and row.get("pattern") == "missing_dependency"
        and float(row.get("score", 0) or 0) >= 3
        for row in ranked
    )

    if tool_name != "cmd_run" or not has_missing_dep:
        return None

    # Strict threshold: only create if capability is absent.
    existing = set(c.get("tool") for c in state.initial_audit_candidates if isinstance(c, dict))
    if "dep_readiness_check" in existing:
        return None

    return {
        "name": "dep_readiness_check",
        "category": "health",
        "description": "Check dependency readiness before executing tests or scripts.",
        "args_spec_json": "[{\"name\":\"target\",\"type\":\"str\",\"optional\":true}]",
        "returns_desc": "all_ok, missing_dependencies, summary",
    }


def _get_tool_path(repo_path: str, tool_name: str) -> Optional[str]:
    base = os.path.join(repo_path, "ai_repo_tools", "tools")
    categories = ["discovery", "planning", "evaluation", "reading", "execution", "health", "toolmaker"]
    for cat in categories:
        p = os.path.join(base, cat, tool_name, "command.py")
        if os.path.isfile(p):
            return f"ai_repo_tools/tools/{cat}/{tool_name}/command.py"
    return None


def _get_validation_cmd(repo_path: str, tool_name: str) -> Optional[str]:
    """Deterministic validation command target for cmd_run (python mode)."""
    # Prefer executing the tool's command module directly as a bounded sanity probe.
    return _get_tool_path(repo_path, tool_name)


def _select_agent_core_step(state: AgentState) -> Optional[dict]:
    """Bounded self-upgrade loop for the agent core policy layer."""
    if not state.artifacts.get("agent_core_audit_done"):
        return {"tool": "agent_audit", "args": []}

    if not state.artifacts.get("agent_core_improve_done"):
        return {"tool": "agent_improver", "args": []}

    if not state.artifacts.get("agent_core_lint_done"):
        return {"tool": "lint_check", "args": ["agent/"]}

    if not state.agent_core_reaudit_done:
        return {"tool": "agent_audit", "args": ["recheck"]}

    state.status = "complete"
    return None


def _select_game_builder_step(state: AgentState) -> Optional[dict]:
    """Build a unique game via small-builder orchestration (no big builder)."""
    if "repo_map" not in state.tools_used:
        return {"tool": "repo_map", "args": []}

    if "game_v2_pipeline_orchestrator" not in state.tools_used:
        output_dir = state.game_builder_output_dir or "agent_aish_tests"
        return {
            "tool": "game_v2_pipeline_orchestrator",
            "args": [output_dir, "small-builders-only"],
        }

    state.status = "complete"
    return None


def _extract_tool_name(goal: str) -> Optional[str]:
    m = re.search(
        r'(?:create|make|new|add|scaffold)\s+tool\s+(?:called|named\s+)?([a-z][a-z0-9_]*)',
        goal, re.IGNORECASE,
    )
    return m.group(1).lower() if m else None


def _extract_tool_category(goal: str) -> str:
    m = re.search(r'\b(discovery|planning|evaluation|reading|execution|health|toolmaker)\b', goal, re.IGNORECASE)
    return m.group(1).lower() if m else "health"


def _extract_tool_description(goal: str) -> Optional[str]:
    m = re.search(r'\b(?:that|which|to)\s+(.+?)(?:\s+in\s+\w+|$)', goal, re.IGNORECASE)
    return m.group(1).strip() if m else None


def is_agent_file(path: str) -> bool:
    """Check if a file is part of the agent codebase."""
    agent_prefixes = ("agent/", "ai_repo_tools/")
    return path.startswith(agent_prefixes)


_ORIENTATION_DOC_NAMES = {"ai_start_here.md", "start_here.md", "readme.md"}
_GUIDANCE_DOC_NAMES = _ORIENTATION_DOC_NAMES | {"build_order.md"}


def _is_orientation_doc(path: str) -> bool:
    return path.split("/")[-1].lower() in _ORIENTATION_DOC_NAMES


def _is_guidance_doc(path: str) -> bool:
    return path.split("/")[-1].lower() in _GUIDANCE_DOC_NAMES


def _extract_referenced_paths_from_text(text: str) -> List[str]:
    """Extract explicit path-like references from doc text in first-seen order."""
    refs: List[str] = []
    seen = set()

    # Common markdown/code-style path references: `ai_repo_tools/README.md`
    for match in re.findall(r"`([^`]+)`", text):
        candidate = match.strip().replace("\\", "/")
        if "/" in candidate or candidate.lower().endswith((".md", ".py")):
            if candidate not in seen:
                seen.add(candidate)
                refs.append(candidate)

    # Plain list lines such as: 1. ai_repo_tools/BUILD_ORDER.md
    for raw_line in text.splitlines():
        line = raw_line.strip().lstrip("-*").strip()
        line = re.sub(r"^\d+\.\s*", "", line)
        if not line:
            continue
        candidate = line.split()[0].strip().strip("`'\"").replace("\\", "/")
        if "/" in candidate and candidate.lower().endswith((".md", ".py")):
            if candidate not in seen:
                seen.add(candidate)
                refs.append(candidate)

    return refs


def _pick_first_existing_reference(refs: List[str], state: AgentState, current_doc: str = "") -> Optional[str]:
    """Pick first unread known file referenced by orientation doc content."""
    if not refs:
        return None

    known = set(state.known_files)

    # Tiny second-hop continuation: after README, prefer BUILD_ORDER if explicitly referenced.
    if current_doc.split("/")[-1].lower() == "readme.md":
        build_order_refs = [r for r in refs if r.split("/")[-1].lower() == "build_order.md"]
        for ref in build_order_refs:
            if ref in known and ref not in state.read_files:
                return ref
        for candidate in state.known_files:
            if candidate in state.read_files:
                continue
            if candidate.split("/")[-1].lower() == "build_order.md":
                return candidate

    # Prefer docs first, but keep original first-seen order from the doc.
    doc_refs = [r for r in refs if r.lower().endswith(".md")]
    other_refs = [r for r in refs if not r.lower().endswith(".md")]
    refs_sorted = doc_refs + other_refs

    for ref in refs_sorted:
        if ref in known and ref not in state.read_files:
            return ref

        # Allow basename-only match as fallback (e.g., BUILD_ORDER.md)
        basename = ref.split("/")[-1]
        if not basename:
            continue
        for candidate in state.known_files:
            if candidate in state.read_files:
                continue
            if candidate.split("/")[-1] == basename:
                return candidate

    return None


def _pick_post_build_order_target(state: AgentState) -> Optional[str]:
    """Prefer high-signal tool-core files immediately after BUILD_ORDER.md."""
    preferred = [
        "ai_repo_tools/main.py",
        "ai_repo_tools/repo_map/README.md",
        "ai_repo_tools/symbol_graph/README.md",
        "ai_repo_tools/change_impact/README.md",
        "ai_repo_tools/test_select/README.md",
    ]
    known = set(state.known_files)
    for candidate in preferred:
        if candidate in known and candidate not in state.read_files:
            return candidate
    return None


def _pick_post_main_target(state: AgentState) -> Optional[str]:
    """Prefer tool-core implementation files immediately after ai_repo_tools/main.py."""
    preferred = [
        "ai_repo_tools/tools/discovery/repo_map/command.py",
        "ai_repo_tools/tools/reading/ai_read/command.py",
        "ai_repo_tools/tools/health/test_select/command.py",
        "ai_repo_tools/tools/execution/cmd_run/command.py",
        "ai_repo_tools/tools/health/env_check/command.py",
    ]
    known = set(state.known_files)
    for candidate in preferred:
        if candidate in known and candidate not in state.read_files:
            return candidate

    # Allow prefixed known file paths (e.g., mini-codex/ai_repo_tools/...).
    for suffix in preferred:
        for candidate in state.known_files:
            if candidate in state.read_files:
                continue
            if candidate.replace("\\", "/").endswith(suffix):
                return candidate
    return None


def select_related_file(state: AgentState) -> Optional[str]:
    """
    Improved follow-up file selection with frequency-based ranking.
    
    Logic:
    1. Extract imported local module names from already-read files
    2. Count frequency of each import reference in the source file
    3. Select unread file matching highest-frequency import (deterministic, alphabetical tiebreaker)
    4. Fall back to same-directory .py files if no matches
    """
    import json
    import os
    
    if not state.trace or not state.read_files:
        return None

    # Tiny orientation/guidance-aware follow-up: if last read is a guidance doc,
    # continue along explicit referenced known files before generic utility scripts.
    if (
        state.last_read_file
        and _is_guidance_doc(state.last_read_file)
    ):
        try:
            path = os.path.join(state.repo_path, state.last_read_file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                doc_text = f.read()
            refs = _extract_referenced_paths_from_text(doc_text)
            referenced_candidate = _pick_first_existing_reference(refs, state, current_doc=state.last_read_file)
            if referenced_candidate:
                return referenced_candidate
        except Exception:
            pass

    # Tiny post-BUILD_ORDER preference before generic import/frequency fallback.
    if state.last_read_file and state.last_read_file.split("/")[-1].lower() == "build_order.md":
        preferred = _pick_post_build_order_target(state)
        if preferred:
            return preferred

    # Tiny post-main preference: after dispatcher entrypoint, move into tool-core
    # implementations before generic utility-style fallback heuristics.
    if state.last_read_file and state.last_read_file.replace("\\", "/").endswith("ai_repo_tools/main.py"):
        preferred = _pick_post_main_target(state)
        if preferred:
            return preferred

    # Extract imported local modules from ai_read results in trace
    imported_modules = set()
    for step in state.trace:
        if step.get("tool") == "ai_read" and step.get("result", {}).get("success"):
            evidence = step["result"].get("evidence", "")
            if evidence.startswith("{"):
                try:
                    data = json.loads(evidence)
                    for imp in data.get("imports", []):
                        # Parse import like "module.name" or "module.sub.name"
                        parts = imp.split(".")
                        if len(parts) >= 1:
                            module_name = parts[0]
                            # Only consider local modules (roughly: not starting with _)
                            if not module_name.startswith("_"):
                                imported_modules.add(module_name)
                except:
                    pass
    
    if not imported_modules:
        return None
    
    # Count frequency of each import in the last-read file
    import_frequency = {}
    if state.last_read_file:
        try:
            file_path = os.path.join(state.repo_path, state.last_read_file)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_text = f.read()
            
            for module_name in imported_modules:
                # Simple frequency count: whole-word matches of module name
                count = source_text.count(module_name)
                import_frequency[module_name] = count
        except:
            # If reading fails, fall back to zero frequency for all
            import_frequency = {m: 0 for m in imported_modules}
    
    # Sort by frequency (descending), then alphabetically (for determinism)
    sorted_imports = sorted(import_frequency.items(), key=lambda x: (-x[1], x[0]))
    
    # Try to find unread files matching imported modules in frequency order
    for module_name, _freq in sorted_imports:
        for candidate in state.known_files:
            if (candidate not in state.read_files and 
                candidate.endswith(".py") and 
                not is_agent_file(candidate) and
                candidate.split("/")[-1] == f"{module_name}.py"):
                return candidate
    
    # Fall back to same-directory unread .py files
    if state.last_read_file:
        dir_path = state.last_read_file.rsplit("/", 1)[0] if "/" in state.last_read_file else ""
        prefix = dir_path + "/" if dir_path else ""
        for f in state.known_files:
            if f not in state.read_files and f.endswith(".py") and f.startswith(prefix) and not is_agent_file(f):
                return f
    
    return None


def should_stop(state: AgentState, max_steps: int) -> bool:
    if state.status != "running":
        return True
    if state.steps_taken >= max_steps:
        return True
    return False


# --- cmd_run planner helpers ---

_RUN_KEYWORDS = {"run", "test", "tests", "verify", "check", "execute", "pytest", "validate"}


def _goal_wants_execution(goal: str) -> bool:
    """Return True if the goal contains execution-intent keywords."""
    words = set(goal.lower().split())
    return bool(words & _RUN_KEYWORDS)


def _extract_run_target(state: AgentState) -> Optional[str]:
    """
    Pick the best pytest target from known_files.
    Prefers a tests/ directory or a test_*.py file.
    Returns a relative path string, or None (whole-repo pytest).
    """
    # Prefer a tests/ directory if it appears in known_files
    for f in state.known_files:
        parts = f.split("/")
        if "tests" in parts:
            return "tests/"

    # Prefer any test_*.py file
    for f in state.known_files:
        name = f.split("/")[-1]
        if name.startswith("test_") and name.endswith(".py"):
            return f

    return None


def _goal_intent(goal: str) -> str:
    """Infer coarse intent bucket from goal text for better tool routing."""
    g = goal.lower()

    quality_tokens = {"quality", "score", "lint", "risk", "evaluate"}
    execution_tokens = {"run", "test", "verify", "execute", "validate", "pytest"}
    readiness_tokens = {"preflight", "readiness", "setup", "dependency", "dependencies", "env", "environment"}
    analysis_tokens = {"analyze", "inspect", "understand", "map", "discover"}
    review_tokens = {"review", "audit"}
    architecture_tokens = {"architecture", "design", "structure", "module", "dependency"}

    words = set(re.findall(r"[a-zA-Z_]+", g))
    if words & readiness_tokens:
        return "readiness"
    if words & execution_tokens:
        return "execution"
    if words & quality_tokens:
        return "quality"
    if words & architecture_tokens:
        return "architecture"
    if words & review_tokens:
        return "review"
    if words & analysis_tokens:
        return "analysis"
    return "general"
