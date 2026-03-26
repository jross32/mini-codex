import os
from typing import Optional, Dict, Any, Callable
from agent.state import create_initial_state, AgentState
from agent.planner import select_next_tool, should_stop
from agent.tool_runner import run_tool, parse_repo_map_result
from agent.evaluator import evaluate_step
from agent.memory import write_step_log
from agent.tool_policy import extract_planned_reads_from_fast_process


class RepoAgent:
    def __init__(
        self,
        goal: str,
        repo_path: str,
        max_steps: int = 20,
        memory_file: str = "agent_logs/agent_run.log",
        use_aish_auto: bool = False,
        toolmaker_max_iterations: int = 3,
        progress_callback: Optional[Callable[[str], None]] = None,
    ):
        self.state: AgentState = create_initial_state(
            goal,
            repo_path,
            use_aish_auto=use_aish_auto,
            toolmaker_max_iterations=toolmaker_max_iterations,
        )
        self.max_steps = max_steps
        self.memory_file = os.path.abspath(memory_file)
        self.progress_callback = progress_callback

    def _emit_progress(self, message: str) -> None:
        if not self.progress_callback:
            return
        try:
            self.progress_callback(message)
        except Exception:
            # Progress reporting must never break the agent loop.
            pass

    def execute(self) -> Dict[str, Any]:
        self._emit_progress(
            f"starting goal='{self.state.goal}' max_steps={self.max_steps}"
        )
        while not should_stop(self.state, self.max_steps):
            plan = select_next_tool(self.state)
            if not plan:
                self.state.status = "complete"
                self._emit_progress("planner returned no next tool; marking run complete")
                break

            tool = plan["tool"]
            args = plan.get("args", [])

            self._emit_progress(
                f"step {self.state.steps_taken + 1}: running {tool} args={args}"
            )

            tool_result = run_tool(tool, args, self.state.repo_path, use_aish_auto=self.state.use_aish_auto)
            evaluation = evaluate_step(tool_result, repo_path=self.state.repo_path)

            record = {
                "tool": tool,
                "args": args,
                "result": tool_result,
                "evaluation": evaluation,
            }

            # Memory/logging
            log_entry = write_step_log(self.state, record, self.memory_file)

            # Update state
            self.state.log_step(record)

            self._emit_progress(
                f"step {self.state.steps_taken}: {tool} success={bool(tool_result.get('success'))}"
            )

            if tool_result.get("success") and tool == "repo_map":
                files = parse_repo_map_result(tool_result)
                self.state.known_files = files

            payload = self._parse_payload(tool_result)

            if tool == "fast_process":
                if tool_result.get("success"):
                    try:
                        import json
                        payload = json.loads(tool_result.get("raw_stdout", "{}"))
                        planned_reads = extract_planned_reads_from_fast_process(payload)
                        if planned_reads:
                            self.state.artifacts["planned_reads"] = planned_reads
                        self.state.artifacts["fast_process_success"] = True
                    except Exception:
                        self.state.artifacts.setdefault("fallback_events", []).append(
                            "fast_process_output_parse_failed"
                        )
                else:
                    self.state.artifacts["fast_process_success"] = False
                    self.state.artifacts.setdefault("fallback_events", []).append(
                        "fast_process_failed_fallback_to_standard_read_planner"
                    )

            if tool_result.get("success") and tool == "ai_read":
                self.state.last_read_file = args[0] if args else None
                if self.state.last_read_file:
                    self.state.read_files.add(self.state.last_read_file)
                    self.state.ai_reads_done += 1
                    # If this is not the first ai_read, it's a follow-up
                    if self.state.ai_reads_done > 1:
                        self.state.follow_up_reads_done += 1

            if tool == "friction_summarizer" and tool_result.get("success"):
                self.state.friction_step_done = True
                self.state.friction_report = payload if isinstance(payload, dict) else None
                self.state.artifacts["friction_report"] = payload

            if tool == "agent_audit" and self.state.agent_core_mode and tool_result.get("success"):
                recommendations = payload.get("recommendations", []) if isinstance(payload, dict) else []
                self.state.agent_core_recommendations = recommendations
                self.state.artifacts["agent_core_recommendations"] = recommendations
                if args and args[0] == "recheck":
                    self.state.agent_core_reaudit_done = True
                    self.state.agent_core_done = True
                    self.state.status = "complete"
                else:
                    self.state.artifacts["agent_core_audit_done"] = True
                    self.state.agent_core_substep = "improve"

            if tool == "agent_improver" and self.state.agent_core_mode and tool_result.get("success"):
                self.state.artifacts["agent_core_improve_done"] = True
                self.state.artifacts["agent_core_improver_payload"] = payload
                self.state.agent_core_substep = "lint"

            if tool == "lint_check" and self.state.agent_core_mode:
                if tool_result.get("success"):
                    self.state.artifacts["agent_core_lint_done"] = True
                    self.state.agent_core_substep = "recheck"
                else:
                    self.state.status = "failed"
                    self._emit_progress("agent-core lint_check failed; stopping run")
                    break

            if tool == "tool_audit" and tool_result.get("success"):
                candidates = payload.get("candidates", []) if isinstance(payload, dict) else []
                self.state.artifacts["tool_audit_candidates_raw"] = candidates
                if candidates:
                    self.state.toolmaker_target = candidates[0].get("tool")
                    self.state.artifacts["toolmaker_target"] = candidates[0].get("tool")

                if not self.state.toolmaker_audit_done:
                    self.state.toolmaker_audit_done = True
                    self.state.initial_audit_candidates = []
                elif not self.state.toolmaker_reaudit_done:
                    self.state.toolmaker_reaudit_done = True
                    self.state.artifacts["toolmaker_reaudit"] = payload
                    self.state.artifacts["toolmaker_reaudit_pass"] = self._evaluate_reaudit()
                    self.state.status = "complete"

            if tool == "toolmaker" and tool_result.get("success"):
                created = payload.get("files_created", []) if isinstance(payload, dict) else []
                created_tool = payload.get("tool") if isinstance(payload, dict) else None
                if created:
                    self.state.artifacts["toolmaker_created_file"] = created[0]
                    self.state.artifacts["toolmaker_current_tool_path"] = created[0]
                if created_tool and created_tool not in self.state.toolmaker_created_tools:
                    self.state.toolmaker_created_tools.append(created_tool)
                self.state.toolmaker_substep = "lint"

            if tool == "tool_improver" and tool_result.get("success"):
                improved_tool = payload.get("tool") if isinstance(payload, dict) else None
                if improved_tool and improved_tool not in self.state.toolmaker_improved_tools:
                    self.state.toolmaker_improved_tools.append(improved_tool)
                if improved_tool:
                    path = self._tool_path_for(improved_tool)
                    if path:
                        self.state.artifacts["toolmaker_current_tool_path"] = path
                self.state.toolmaker_substep = "lint"

            if tool == "lint_check" and self.state.toolmaker_mode:
                if tool_result.get("success"):
                    self.state.toolmaker_substep = "validate"
                else:
                    self._skip_current_candidate("lint_failed")

            if tool == "cmd_run" and self.state.toolmaker_mode:
                if tool_result.get("success"):
                    self.state.toolmaker_substep = "improve"
                    self.state.toolmaker_iteration += 1
                else:
                    self._skip_current_candidate("validate_failed")

            # if model identifies no better step after test_select, consume one recommendation
            if tool == "test_select":
                # Try to consume at most one recommendation
                if tool_result.get("success"):
                    try:
                        import json
                        output = json.loads(tool_result.get("raw_stdout", "{}"))
                        recommended = output.get("recommended_files", [])
                        if recommended:
                            first_rec_file = recommended[0].get("file")
                            if first_rec_file and first_rec_file not in self.state.read_files:
                                # Read the recommended file
                                rec_result = run_tool(
                                    "ai_read",
                                    [first_rec_file],
                                    self.state.repo_path,
                                    use_aish_auto=self.state.use_aish_auto,
                                )
                                rec_eval = evaluate_step(rec_result, repo_path=self.state.repo_path)
                                rec_record = {
                                    "tool": "ai_read",
                                    "args": [first_rec_file],
                                    "result": rec_result,
                                    "evaluation": rec_eval,
                                    "source": "test_select_recommendation"
                                }
                                log_entry = write_step_log(self.state, rec_record, self.memory_file)
                                self.state.log_step(rec_record)
                                if rec_result.get("success"):
                                    self.state.last_read_file = first_rec_file
                                    self.state.read_files.add(first_rec_file)
                                    self.state.ai_reads_done += 1
                    except Exception:
                        pass
                
                # Add synthesis summary now; loop continues so planner can run cmd_run if needed
                if self.state.read_files:
                    synthesis = self._create_synthesis_summary()
                    self.state.artifacts["synthesis"] = synthesis
                # Do NOT force complete here — let the planner decide (cmd_run rule 4.5 may fire)

            if self.state.toolmaker_mode and evaluation["success"] is False:
                if tool in ("tool_improver", "toolmaker"):
                    self._skip_current_candidate(f"{tool}_failed")
                    self._emit_progress(f"{tool} failed; skipping candidate and continuing")
                    continue
                if tool in ("friction_summarizer", "tool_audit"):
                    self.state.status = "failed"
                    self._emit_progress(f"{tool} failed in toolmaker mode; stopping run")
                    break

            if self.state.agent_core_mode and evaluation["success"] is False:
                if tool in ("agent_audit", "agent_improver"):
                    self.state.status = "failed"
                    self._emit_progress(f"{tool} failed in agent-core mode; stopping run")
                    break

            if evaluation["success"] is False and tool not in ("repo_map", "env_check", "fast_process", "lint_check"):
                # avoid infinite loops on repeated failure
                # env_check and lint_check are advisory and must not abort the run
                self.state.status = "failed"
                self._emit_progress(f"{tool} failed with hard-stop policy; stopping run")
                break

        final_summary = self._summary()
        self._emit_progress(
            f"finished status={self.state.status} steps={self.state.steps_taken}"
        )
        return {
            "final_summary": final_summary,
            "trace": self.state.trace,
            "status": self.state.status,
        }

    def _summary(self) -> str:
        synthesis = self.state.artifacts.get("synthesis", "")
        return (
            f"Goal: {self.state.goal}. "
            f"Steps: {self.state.steps_taken}. "
            f"Status: {self.state.status}. "
            f"Tools used: {', '.join(self.state.tools_used)}"
            f" Toolmaker iteration: {self.state.toolmaker_iteration}/{self.state.toolmaker_max_iterations}."
            f"{f' Synthesis: {synthesis}' if synthesis else ''}"
        )

    def _parse_payload(self, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        raw = tool_result.get("raw_stdout", "{}")
        if not isinstance(raw, str):
            return {}
        try:
            import json
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    def _tool_path_for(self, tool_name: str) -> Optional[str]:
        categories = ["discovery", "planning", "evaluation", "reading", "execution", "health", "toolmaker"]
        for cat in categories:
            rel = f"ai_repo_tools/tools/{cat}/{tool_name}/command.py"
            abs_path = os.path.join(self.state.repo_path, rel)
            if os.path.isfile(abs_path):
                return rel
        return None

    def _skip_current_candidate(self, reason: str) -> None:
        target = self.state.toolmaker_target or "unknown"
        fails = self.state.toolmaker_candidate_failures.get(target, 0) + 1
        self.state.toolmaker_candidate_failures[target] = fails
        self.state.artifacts.setdefault("toolmaker_skips", []).append(
            {
                "iteration": self.state.toolmaker_iteration,
                "tool": target,
                "reason": reason,
                "fail_count": fails,
            }
        )
        if fails > self.state.toolmaker_max_failures_per_candidate:
            self.state.artifacts.setdefault("toolmaker_hard_skips", []).append(target)
        self.state.toolmaker_substep = "improve"
        self.state.toolmaker_iteration += 1

    def _evaluate_reaudit(self) -> bool:
        """Re-audit pass criteria: no regression plus evidence of progress."""
        before_raw = self.state.artifacts.get("initial_audit_candidates", [])
        after_payload = self.state.artifacts.get("toolmaker_reaudit", {})
        after_raw = after_payload.get("candidates", []) if isinstance(after_payload, dict) else []

        before_scores = {
            c.get("tool"): int(c.get("baseline_score", c.get("score", 0)) or 0)
            for c in before_raw if isinstance(c, dict) and c.get("tool")
        }
        after_scores = {
            c.get("tool"): int(c.get("baseline_score", c.get("score", 0)) or 0)
            for c in after_raw if isinstance(c, dict) and c.get("tool")
        }

        no_regression = True
        improvement_found = False
        for tool, old_score in before_scores.items():
            new_score = after_scores.get(tool, old_score)
            if new_score < old_score:
                no_regression = False
            if new_score > old_score:
                improvement_found = True

        if self.state.toolmaker_improved_tools or self.state.toolmaker_created_tools:
            improvement_found = True

        return bool(no_regression and improvement_found)

    def _create_synthesis_summary(self) -> str:
        if not self.state.read_files:
            return ""
        
        files_read = sorted(self.state.read_files)
        main_files = [f for f in files_read if not f.startswith(("agent/", "ai_repo_tools/"))]
        
        # Simple heuristics for likely entry point
        entry_candidates = [f for f in main_files if f.endswith(("__init__.py", "main.py", "app.py", "run.py"))]
        likely_entry = entry_candidates[0] if entry_candidates else (main_files[0] if main_files else "unknown")
        
        # Group by directory
        dirs = {}
        for f in main_files:
            dir_name = f.rsplit("/", 1)[0] if "/" in f else "root"
            if dir_name not in dirs:
                dirs[dir_name] = []
            dirs[dir_name].append(f)
        
        dir_summary = ", ".join([f"{d}({len(fs)} files)" for d, fs in dirs.items()])
        
        # Analyze cross-file relationships from ai_read results
        relationships = self._analyze_relationships()
        
        base_summary = f"Read {len(main_files)} main files. Likely entry: {likely_entry}. Structure: {dir_summary}."
        if relationships:
            base_summary += f" Relationships: {relationships}."
        
        unknown_parts = ["subdirs not explored"]
        if len(main_files) < len([f for f in self.state.known_files if not f.startswith(("agent/", "ai_repo_tools/"))]):
            unknown_parts.append("some files not read")
        
        base_summary += f" Unknown: {', '.join(unknown_parts)}."
        
        return base_summary

    def _analyze_relationships(self) -> str:
        """Analyze basic cross-file relationships from ai_read results."""
        file_data = {}
        
        # Extract data from ai_read results in trace
        for step in self.state.trace:
            if step.get("tool") == "ai_read" and step.get("result", {}).get("success"):
                evidence = step["result"].get("evidence", "")
                if evidence.startswith("{"):
                    try:
                        import json
                        data = json.loads(evidence)
                        path = data.get("path")
                        if path in self.state.read_files:
                            file_data[path] = {
                                "imports": data.get("imports", []),
                                "classes": data.get("classes", []),
                                "functions": data.get("functions", [])
                            }
                    except:
                        pass
        
        if len(file_data) < 2:
            return ""
        
        relationships = []
        
        # Detect import relationships
        for file_path, data in file_data.items():
            for imp in data.get("imports", []):
                # Parse import like "module.name" or "module.sub.name"
                parts = imp.split(".")
                if len(parts) >= 2:
                    module_name = parts[0]
                    imported_name = parts[-1]  # Last part is the name
                    module_file = f"{module_name}.py"
                    if module_file in file_data and module_file != file_path:
                        target_data = file_data[module_file]
                        if imported_name in target_data.get("functions", []) or imported_name in target_data.get("classes", []):
                            relationships.append(f"{file_path.split('.')[0]} imports {imported_name} from {module_name}")
        
        # Add functionality descriptions
        for file_path, data in file_data.items():
            if data.get("functions"):
                func_names = [f.split("(")[0] for f in data["functions"] if "(" in f and f.split("(")[0] not in ["wrapper"]]  # Skip wrapper
                if func_names:
                    relationships.append(f"{file_path.split('.')[0]} defines {', '.join(func_names[:3])}")
            if data.get("classes"):
                if data["classes"]:
                    relationships.append(f"{file_path.split('.')[0]} defines {', '.join(data['classes'][:2])} class")
        
        return "; ".join(relationships[:5])  # Limit to 5 relationships max


def run_agent(
    goal: str,
    repo_path: str,
    max_steps: int = 20,
    memory_file: str = "agent_logs/agent_run.log",
    use_aish_auto: bool = False,
    toolmaker_max_iterations: int = 3,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    agent = RepoAgent(
        goal=goal,
        repo_path=repo_path,
        max_steps=max_steps,
        memory_file=memory_file,
        use_aish_auto=use_aish_auto,
        toolmaker_max_iterations=toolmaker_max_iterations,
        progress_callback=progress_callback,
    )
    return agent.execute()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run deterministic repo tool agent")
    parser.add_argument("--goal", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--memory-file", default="agent_logs/agent_run.log")

    args = parser.parse_args()

    result = run_agent(args.goal, args.repo, args.max_steps, args.memory_file)
    print("FINAL SUMMARY")
    print(result["final_summary"])
    print("TRACE")
    for step in result["trace"]:
        print(step)
