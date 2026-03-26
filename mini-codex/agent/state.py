from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
from agent.core_state import load_agent_core_state


@dataclass
class AgentState:
    goal: str
    repo_path: str
    steps_taken: int = 0
    tools_used: List[str] = field(default_factory=list)
    known_files: List[str] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    status: str = "running"
    trace: List[Dict[str, Any]] = field(default_factory=list)
    follow_up_allowed: bool = False
    last_read_file: str = ""
    read_files: set = field(default_factory=set)
    follow_up_reads_done: int = 0
    ai_reads_done: int = 0
    use_aish_auto: bool = False
    toolmaker_mode: bool = False
    toolmaker_target: Optional[str] = None
    toolmaker_iteration: int = 0
    toolmaker_max_iterations: int = 3
    toolmaker_substep: str = "improve"
    friction_step_done: bool = False
    toolmaker_audit_done: bool = False
    toolmaker_reaudit_done: bool = False
    friction_report: Optional[Dict[str, Any]] = None
    initial_audit_candidates: List[Dict[str, Any]] = field(default_factory=list)
    toolmaker_improved_tools: List[str] = field(default_factory=list)
    toolmaker_created_tools: List[str] = field(default_factory=list)
    toolmaker_candidate_failures: Dict[str, int] = field(default_factory=dict)
    toolmaker_max_failures_per_candidate: int = 1
    agent_core_mode: bool = False
    agent_core_substep: str = "audit"
    agent_core_done: bool = False
    agent_core_reaudit_done: bool = False
    agent_core_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    game_builder_mode: bool = False
    game_builder_output_dir: str = "agent_aish_tests"

    def log_step(self, record: Dict[str, Any]):
        self.trace.append({"timestamp": datetime.utcnow().isoformat() + "Z", **record})
        self.steps_taken = len(self.trace)
        if "tool" in record and record["tool"]:
            if record["tool"] not in self.tools_used:
                self.tools_used.append(record["tool"])


def create_initial_state(
    goal: str,
    repo_path: str,
    use_aish_auto: bool = False,
    toolmaker_max_iterations: int = 3,
) -> AgentState:
    # For broad goals, allow follow-up reads
    follow_up_allowed = any(word in goal.lower() for word in ["inspect", "explore", "understand", "analyze", "review"])
    env_auto = os.getenv("AISH_AUTO_MODE", "0") == "1"
    auto_mode = bool(use_aish_auto or env_auto or follow_up_allowed)
    toolmaker_mode = any(
        phrase in goal.lower()
        for phrase in [
            "improve toolkit", "improve tools", "audit tools", "audit toolkit",
            "create tool", "make tool", "new tool", "add tool", "scaffold tool",
        ]
    )
    agent_core_mode = any(
        phrase in goal.lower()
        for phrase in [
            "upgrade agent core",
            "improve agent core",
            "improve orchestrator",
            "upgrade orchestrator",
        ]
    )
    core_state = load_agent_core_state(repo_path)
    max_failures = int(core_state.get("toolmaker_max_failures_per_candidate", 1) or 1)

    goal_lower = goal.lower()
    game_builder_mode = any(
        phrase in goal_lower
        for phrase in [
            "build adventure game",
            "adventure game",
            "build game",
            "unique game",
            "rpg game",
        ]
    ) and ("small builder" in goal_lower or "smaller builder" in goal_lower or "small builders" in goal_lower)

    if "agent_aish_tests" in goal_lower:
        game_builder_output_dir = "agent_aish_tests"
    else:
        game_builder_output_dir = "agent_aish_tests"

    return AgentState(
        goal=goal,
        repo_path=repo_path,
        follow_up_allowed=follow_up_allowed,
        use_aish_auto=auto_mode,
        toolmaker_mode=toolmaker_mode,
        toolmaker_max_iterations=max(1, int(toolmaker_max_iterations)),
        toolmaker_max_failures_per_candidate=max(1, max_failures),
        agent_core_mode=agent_core_mode,
        game_builder_mode=game_builder_mode,
        game_builder_output_dir=game_builder_output_dir,
    )
