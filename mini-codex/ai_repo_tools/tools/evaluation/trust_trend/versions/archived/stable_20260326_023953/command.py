import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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


def _compute_trust_score(trace: List[Dict], successful_peers: int) -> Dict:
    metrics = _collect_eval_metrics(trace)
    tools_used: List[str] = []
    for step in trace:
        tool = step.get("tool") if isinstance(step, dict) else None
        if tool and tool not in tools_used:
            tools_used.append(tool)

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
    return {
        "trust_score": round(trust_score, 3),
        "self_improvement_ready": self_improve,
        "collaboration_ready": collaborates,
        **metrics,
    }


def _linear_slope(values: List[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    num = 0.0
    den = 0.0
    for i, y in enumerate(values):
        dx = i - x_mean
        num += dx * (y - y_mean)
        den += dx * dx
    if den == 0.0:
        return 0.0
    return num / den


def _classify_trend(values: List[float]) -> Dict:
    if len(values) < 3:
        return {
            "signal": "insufficient_data",
            "slope": 0.0,
            "delta": 0.0,
        }

    slope = _linear_slope(values)
    delta = values[-1] - values[0]

    if slope >= 0.005 and delta >= 0.02:
        signal = "improving"
    elif slope <= -0.005 and delta <= -0.02:
        signal = "declining"
    else:
        signal = "stalling"

    return {
        "signal": signal,
        "slope": round(slope, 4),
        "delta": round(delta, 4),
    }


def _parse_worker_log(log_path: Path) -> List[Dict]:
    episodes: List[Dict] = []
    current_trace: List[Dict] = []
    started_at: Optional[str] = None

    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return episodes

    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            event = json.loads(raw)
        except Exception:
            continue

        steps_taken = None
        state = event.get("state")
        if isinstance(state, dict):
            steps_taken = state.get("steps_taken")

        if steps_taken == 0 and current_trace:
            episodes.append({"started_at": started_at, "trace": current_trace})
            current_trace = []
            started_at = None

        if started_at is None:
            started_at = event.get("timestamp")

        current_trace.append(event)

    if current_trace:
        episodes.append({"started_at": started_at, "trace": current_trace})

    return episodes


def run_trust_trend(repo_path: str, lookback: Optional[int] = 20, peers: Optional[int] = 2) -> Tuple[int, Dict]:
    t0 = time.monotonic()

    try:
        lookback_n = 20 if lookback is None else int(lookback)
        peers_n = 2 if peers is None else int(peers)
    except (TypeError, ValueError):
        return 2, {
            "success": False,
            "error": "invalid_argument",
            "detail": "lookback and peers must be integers",
        }

    if lookback_n <= 0:
        return 2, {
            "success": False,
            "error": "invalid_argument",
            "detail": "lookback must be > 0",
        }

    if peers_n < 0:
        return 2, {
            "success": False,
            "error": "invalid_argument",
            "detail": "peers must be >= 0",
        }

    logs_dir = Path(repo_path) / "agent_logs"
    if not logs_dir.exists():
        return 2, {
            "success": False,
            "error": "missing_path",
            "detail": "agent_logs directory not found",
            "target": str(logs_dir),
        }

    worker_logs = sorted(logs_dir.glob("orchestrator_*_worker.log"))
    worker_histories: List[Dict] = []

    all_recent_scores: List[float] = []
    for log_path in worker_logs:
        episodes = _parse_worker_log(log_path)
        if not episodes:
            continue

        series = []
        for ep in episodes[-lookback_n:]:
            score_payload = _compute_trust_score(ep.get("trace", []), peers_n)
            series.append(
                {
                    "started_at": ep.get("started_at"),
                    "trust_score": score_payload.get("trust_score", 0.0),
                    "success_rate": score_payload.get("success_rate", 0.0),
                    "self_improvement_ready": score_payload.get("self_improvement_ready", False),
                    "collaboration_ready": score_payload.get("collaboration_ready", False),
                }
            )

        scores = [item["trust_score"] for item in series]
        trend = _classify_trend(scores)
        all_recent_scores.extend(scores)

        worker_histories.append(
            {
                "worker": log_path.name.replace("orchestrator_", "").replace(".log", ""),
                "episodes_considered": len(series),
                "latest_trust_score": round(scores[-1], 3) if scores else 0.0,
                "trend": trend,
                "series": series,
            }
        )

    overall_scores = sorted(
        [
            (item["started_at"], item["trust_score"])
            for worker in worker_histories
            for item in worker.get("series", [])
            if item.get("started_at") is not None
        ],
        key=lambda x: x[0],
    )
    overall_values = [v for _, v in overall_scores][-lookback_n:]
    overall = _classify_trend(overall_values)

    elapsed_ms = round((time.monotonic() - t0) * 1000)
    payload = {
        "success": True,
        "tool": "trust_trend",
        "assumed_successful_peers": peers_n,
        "lookback": lookback_n,
        "workers_analyzed": len(worker_histories),
        "overall": {
            **overall,
            "latest_trust_score": round(overall_values[-1], 3) if overall_values else 0.0,
            "episodes_considered": len(overall_values),
        },
        "workers": worker_histories,
        "elapsed_ms": elapsed_ms,
        "summary": (
            f"Trust trend {overall.get('signal')} across {len(worker_histories)} worker histories "
            f"using last {lookback_n} episode(s) each."
        ),
    }
    return 0, payload


def cmd_trust_trend(repo_path: str, lookback: Optional[int] = 20, peers: Optional[int] = 2):
    code, payload = run_trust_trend(repo_path, lookback=lookback, peers=peers)
    print(json.dumps(payload))
    return code, payload