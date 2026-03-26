from pathlib import Path
import shutil
import sys
import importlib


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
AI_REPO_TOOLS_ROOT = ROOT / "ai_repo_tools"
if str(AI_REPO_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_REPO_TOOLS_ROOT))


from agent.planner import select_next_tool  # noqa: E402
from agent.state import create_initial_state  # noqa: E402


ai_tools_main = importlib.import_module("main")
game_v2_command = importlib.import_module(
    "tools.interactive_systems.gameplay.systems.mechanics.specializations.game_v2.game_v2_pipeline_orchestrator.command"
)
_stable_seed = game_v2_command._stable_seed
run_game_v2_pipeline_orchestrator = game_v2_command.run_game_v2_pipeline_orchestrator


def test_game_builder_planner_branch_sequences_repo_map_then_pipeline():
    state = create_initial_state(
        goal="Build a unique adventure game using smaller builders only in agent_aish_tests",
        repo_path=str(ROOT),
    )

    assert state.game_builder_mode is True
    assert state.game_builder_output_dir == "agent_aish_tests"

    step1 = select_next_tool(state)
    assert step1 == {"tool": "repo_map", "args": []}

    state.tools_used.append("repo_map")
    step2 = select_next_tool(state)
    assert step2["tool"] == "game_v2_pipeline_orchestrator"
    assert step2["args"] == ["agent_aish_tests", "small-builders-only"]

    state.tools_used.append("game_v2_pipeline_orchestrator")
    step3 = select_next_tool(state)
    assert step3 is None
    assert state.status == "complete"


def test_dispatch_forwards_game_pipeline_args():
    output_dir = "agent_aish_tests_dispatch_check"
    profile_seed = "dispatch-seed-regression"
    target_root = ROOT.parent / output_dir
    if target_root.exists():
        shutil.rmtree(target_root)

    try:
        exit_code, payload = ai_tools_main.dispatch_tool(
            str(ROOT),
            "game_v2_pipeline_orchestrator",
            [output_dir, profile_seed],
        )

        assert exit_code == 0
        assert payload["success"] is True
        assert payload["target_dir"] == f"../{output_dir}"
        assert payload["seed"] == _stable_seed(str(ROOT), profile_seed)
        assert (target_root / "game" / "main.py").exists()
    finally:
        if target_root.exists():
            shutil.rmtree(target_root)


def test_pipeline_generates_deeper_gameplay_modules_and_interactive_main():
    target_root = ROOT.parent / "agent_aish_tests_regression"
    if target_root.exists():
        shutil.rmtree(target_root)

    code, payload = run_game_v2_pipeline_orchestrator(
        str(ROOT),
        output_dir="agent_aish_tests_regression",
        profile_seed="small-builders-only",
    )

    try:
        assert code == 0
        assert payload["success"] is True
        assert payload["mode"] == "small_builders_pipeline"
        assert payload["gameplay_depth"] == "preview_plus_interactive_loop"
        assert payload["small_builders_used"] == [
            "directory_structure_generator",
            "python_module_generator",
        ]

        main_file = target_root / "game" / "main.py"
        player_file = target_root / "game" / "systems" / "player.py"
        progression_file = target_root / "game" / "systems" / "progression.py"
        narrative_file = target_root / "game" / "systems" / "narrative.py"

        assert main_file.exists()
        assert player_file.exists()
        assert progression_file.exists()
        assert narrative_file.exists()

        main_text = main_file.read_text(encoding="utf-8")
        assert "def play_loop(theme):" in main_text
        assert "--play" in main_text
    finally:
        if target_root.exists():
            shutil.rmtree(target_root)
