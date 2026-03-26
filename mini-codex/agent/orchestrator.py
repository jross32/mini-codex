import json
import os
from typing import Dict, List

from agent.agent_loop import run_agent
from agent.tool_runner import run_tool


def _worker_log_path(repo_path: str, worker_name: str) -> str:
    return os.path.join(repo_path, "agent_logs", f"orchestrator_{worker_name}.log")


def _emit_progress(message: str) -> None:
    print(f"[orchestrator] {message}", flush=True)


def _summarize_worker(name: str, result: Dict) -> Dict:
    status = result.get("status", "unknown")
    trace = result.get("trace", [])
    tools_used = []
    for step in trace:
        tool = step.get("tool") if isinstance(step, dict) else None
        if tool and tool not in tools_used:
            tools_used.append(tool)

    return {
        "worker": name,
        "status": status,
        "steps": len(trace),
        "tools_used": tools_used,
        "final_summary": result.get("final_summary", ""),
    }


def _collect_eval_metrics(trace: List[Dict]) -> Dict:
    evals = [
        s.get("evaluation", {})
        for s in trace
        if isinstance(s, dict) and isinstance(s.get("evaluation"), dict)
    ]
    if not evals:
        return {
            "success_rate": 0.0,
            "avg_usefulness": 0.0,
            "avg_uncertainty_reduction": 0.0,
            "avg_next_step_quality": 0.0,
        }

    n = float(len(evals))
    success_rate = sum(1 for e in evals if bool(e.get("success"))) / n
    avg_usefulness = sum(float(e.get("usefulness", 0) or 0) for e in evals) / n
    avg_uncertainty = sum(float(e.get("uncertainty_reduction", 0) or 0) for e in evals) / n
    avg_next = sum(float(e.get("next_step_quality", 0) or 0) for e in evals) / n
    return {
        "success_rate": round(success_rate, 3),
        "avg_usefulness": round(avg_usefulness, 3),
        "avg_uncertainty_reduction": round(avg_uncertainty, 3),
        "avg_next_step_quality": round(avg_next, 3),
    }


def _self_improvement_ready(tools_used: List[str]) -> bool:
    toolkit_set = {"tool_audit", "tool_improver", "lint_check"}
    core_set = {"agent_audit", "agent_improver", "lint_check"}
    toolset = set(tools_used)
    return toolkit_set.issubset(toolset) or core_set.issubset(toolset)


def _collaboration_ready(tools_used: List[str], successful_peers: int) -> bool:
    collaboration_signals = 0
    if successful_peers >= 1:
        collaboration_signals += 1
    if successful_peers >= 2:
        collaboration_signals += 1
    if "lint_check" in tools_used:
        collaboration_signals += 1
    if any(t in tools_used for t in ("repo_map", "fast_process", "test_select")):
        collaboration_signals += 1
    return collaboration_signals >= 2


def _benchmark_worker(summary: Dict, trace: List[Dict], successful_peers: int, trust_threshold: float) -> Dict:
    metrics = _collect_eval_metrics(trace)
    tools_used = summary.get("tools_used", [])
    self_improve = _self_improvement_ready(tools_used)
    collaborates = _collaboration_ready(tools_used, successful_peers)

    success_norm = metrics.get("success_rate", 0.0)
    usefulness_norm = min(1.0, (metrics.get("avg_usefulness", 0.0) / 5.0))
    next_norm = min(1.0, (metrics.get("avg_next_step_quality", 0.0) / 5.0))
    self_norm = 1.0 if self_improve else 0.0
    collab_norm = 1.0 if collaborates else 0.0

    trust_score = (
        (0.45 * success_norm)
        + (0.20 * usefulness_norm)
        + (0.20 * next_norm)
        + (0.10 * self_norm)
        + (0.05 * collab_norm)
    )
    trust_score = round(trust_score, 3)

    trusted = bool(
        summary.get("status") in {"complete", "running"}
        and summary.get("steps", 0) >= 3
        and success_norm >= 0.85
        and self_improve
        and collaborates
        and trust_score >= trust_threshold
    )

    return {
        "trusted": trusted,
        "trust_score": trust_score,
        "trust_threshold": trust_threshold,
        "self_improvement_ready": self_improve,
        "collaboration_ready": collaborates,
        **metrics,
    }


def _is_hard_fail_worker(name: str) -> bool:
    if name.startswith("autonomous_worker_"):
        return True
    return name in {"toolkit_upgrade_worker", "quality_gate_worker", "agent_core_upgrade_worker"}


def _can_spawn_more_from_worker(name: str) -> bool:
    if name.startswith("autonomous_worker_"):
        return True
    return name == "agent_core_upgrade_worker"


def _spawn_worker(worker_index: int, base_iterations: int) -> Dict:
    return {
        "name": f"autonomous_worker_{worker_index}",
        "mode": "agent",
        "goal": "upgrade agent core with bounded policy tuning and collaborate safely with peer workers",
        "max_steps": 10,
        "toolmaker_max_iterations": max(1, min(2, int(base_iterations))),
    }


def run_orchestrator_workflow(
    repo_path: str,
    max_iterations: int = 3,
    trust_threshold: float = 0.84,
    max_total_workers: int = 16,
    allow_unbounded_growth: bool = False,
) -> Dict:
    """
    Run a deterministic orchestrator + workers workflow.

    Worker phases:
      1) toolkit_upgrade_worker
      2) repo_inspector_worker
      3) quality_gate_worker
      4) agent_core_upgrade_worker
    """
    iters = max(1, int(max_iterations))
    _emit_progress(
        "starting run "
        f"iterations={iters} trust_threshold={trust_threshold} "
        f"max_total_workers={max_total_workers} allow_unbounded={allow_unbounded_growth}"
    )

    workers: List[Dict] = [
        {
            "name": "toolkit_upgrade_worker",
            "mode": "agent",
            "goal": "improve toolkit with friction-driven iterative upgrades",
            "max_steps": 1 + 1 + (iters * 3) + 1 + 3,
            "toolmaker_max_iterations": iters,
        },
        {
            "name": "repo_inspector_worker",
            "mode": "agent",
            "goal": "inspect architecture and analyze repository structure",
            "max_steps": 12,
            "toolmaker_max_iterations": 1,
        },
        {
            "name": "quality_gate_worker",
            "mode": "tools",
            "tools": [
                {"tool": "repo_health_check", "args": []},
                {"tool": "lint_check", "args": ["agent/"]},
                {"tool": "lint_check", "args": ["aish/"]},
                {"tool": "lint_check", "args": ["ai_repo_tools/"]},
            ],
        },
        {
            "name": "agent_core_upgrade_worker",
            "mode": "agent",
            "goal": "upgrade agent core with bounded policy tuning",
            "max_steps": 8,
            "toolmaker_max_iterations": 1,
        },
    ]

    summaries: List[Dict] = []
    hard_failed = False
    successful_peers = 0
    index = 0
    spawned_workers = 0
    hard_cap = 128 if allow_unbounded_growth else max(1, int(max_total_workers))
    _emit_progress(f"worker cap resolved to {hard_cap}")

    while index < len(workers):
        worker = workers[index]
        _emit_progress(
            f"worker {index + 1}/{len(workers)} starting: {worker['name']} mode={worker.get('mode')}"
        )
        if hard_failed:
            summaries.append(
                {
                    "worker": worker["name"],
                    "status": "skipped",
                    "steps": 0,
                    "tools_used": [],
                    "final_summary": "Skipped due to earlier gate failure.",
                }
            )
            _emit_progress(f"worker {worker['name']} skipped due to earlier hard-fail gate")
            index += 1
            continue

        trace_for_benchmark: List[Dict] = []

        if worker.get("mode") == "tools":
            tool_steps = []
            failed = False
            for entry in worker.get("tools", []):
                tool = entry.get("tool")
                args = entry.get("args", [])
                _emit_progress(f"{worker['name']}: running tool {tool} args={args}")
                tool_result = run_tool(tool, args, repo_path, use_aish_auto=True)
                tool_steps.append({"tool": tool, "success": bool(tool_result.get("success"))})
                _emit_progress(
                    f"{worker['name']}: tool {tool} success={bool(tool_result.get('success'))}"
                )
                if not tool_result.get("success"):
                    failed = True
                    break

            summary = {
                "worker": worker["name"],
                "status": "failed" if failed else "complete",
                "steps": len(tool_steps),
                "tools_used": [s["tool"] for s in tool_steps],
                "final_summary": (
                    "Tool-based quality gate failed."
                    if failed
                    else "Tool-based quality gate passed."
                ),
            }
            trace_for_benchmark = [
                {
                    "evaluation": {
                        "success": bool(s.get("success")),
                        "usefulness": 4 if s.get("success") else 1,
                        "uncertainty_reduction": 3 if s.get("success") else 1,
                        "next_step_quality": 3 if s.get("success") else 1,
                    }
                }
                for s in tool_steps
            ]
        else:
            result = run_agent(
                goal=worker["goal"],
                repo_path=repo_path,
                max_steps=worker["max_steps"],
                memory_file=_worker_log_path(repo_path, worker["name"]),
                use_aish_auto=True,
                toolmaker_max_iterations=worker["toolmaker_max_iterations"],
                progress_callback=lambda msg, name=worker["name"]: _emit_progress(f"{name}: {msg}"),
            )
            summary = _summarize_worker(worker["name"], result)
            trace_for_benchmark = result.get("trace", []) or []

        summary["benchmark"] = _benchmark_worker(
            summary=summary,
            trace=trace_for_benchmark,
            successful_peers=successful_peers,
            trust_threshold=float(trust_threshold),
        )

        summaries.append(summary)
        bench = summary.get("benchmark", {})
        _emit_progress(
            f"worker {worker['name']} completed status={summary.get('status')} steps={summary.get('steps')} "
            f"trust={bench.get('trust_score')} trusted={bench.get('trusted')}"
        )

        if summary["status"] in {"complete", "running"}:
            successful_peers += 1

        if _is_hard_fail_worker(worker["name"]):
            if summary["status"] not in {"complete", "running"}:
                hard_failed = True
                _emit_progress(f"hard-fail gate triggered by {worker['name']}; downstream workers may be skipped")

        if (
            not hard_failed
            and _can_spawn_more_from_worker(worker["name"])
            and summary.get("benchmark", {}).get("trusted")
            and len(workers) < hard_cap
        ):
            spawned_workers += 1
            new_worker = _spawn_worker(spawned_workers, iters)
            workers.append(new_worker)
            summary["spawned_worker"] = new_worker["name"]
            _emit_progress(
                f"{worker['name']} trusted and spawned {new_worker['name']} "
                f"(total workers queued={len(workers)})"
            )

        index += 1

    overall_success = all(s["status"] in {"complete", "running", "skipped"} for s in summaries)
    payload = {
        "success": overall_success,
        "mode": "orchestrator_workers",
        "allow_unbounded_growth": bool(allow_unbounded_growth),
        "max_total_workers": hard_cap,
        "workers_spawned": spawned_workers,
        "workers": summaries,
        "summary": (
            f"Orchestrator ran {len(summaries)} worker phases with "
            f"{len([s for s in summaries if s['status'] in {'complete', 'running'}])} successful executions."
        ),
    }

    out_path = os.path.join(repo_path, "agent_logs", "orchestrator_summary.json")
    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
    except Exception:
        payload["summary"] += " Failed to write orchestrator_summary.json."

    _emit_progress(
        f"run finished success={payload.get('success')} "
        f"workers_executed={len(summaries)} workers_spawned={spawned_workers}"
    )

    return payload
