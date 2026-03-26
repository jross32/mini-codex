"""Candidate lifecycle and promotion pipeline for evolvable tools.

v1 intentionally pilots one low-risk tool (`trust_trend`) before generalization.
Improvements: rollback snapshots, exit code distinction, gate config, richer reports,
audit logs, deprecation support, canary gates, plugin hooks.
"""

from __future__ import annotations

import io
import json
import shutil
import statistics
import time
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


SCHEMA_VERSION = "promotion.v2"
PILOT_TOOL = "trust_trend"
PILOT_CATEGORY = "evaluation"
REQUIRED_PAYLOAD_KEYS = {"success", "tool", "overall", "workers", "summary"}
MAX_STABLE_SNAPSHOTS = 5  # Keep last 5 stable versions for rollback


@dataclass
class ToolPaths:
    live_command: Path
    versions_root: Path
    stable_command: Path
    candidate_root: Path
    archived_root: Path
    stable_snapshots_root: Path


def _now_stamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S", time.gmtime())


def _load_gate_config(repo_path: str, tool_name: str) -> Dict[str, Any]:
    """Load gate configuration from aish/promotion_gates.json, falling back to defaults."""
    gate_config_path = Path(repo_path) / "aish" / "promotion_gates.json"
    defaults = {
        "correctness_floor": 1.0,
        "max_slowdown_pct": 5.0,
        "min_runs": 3,
        "required_keys": sorted(REQUIRED_PAYLOAD_KEYS),
        "enable_canary": False,
        "canary_sample_count": 10,
    }
    
    if gate_config_path.exists():
        try:
            config_data = json.loads(gate_config_path.read_text(encoding="utf-8"))
            tool_config = config_data.get(tool_name, config_data.get("default", {}))
            return {**defaults, **tool_config}
        except Exception:
            pass
    
    return defaults


def _write_audit_event(repo_path: str, tool_name: str, event: Dict[str, Any]) -> None:
    """Append promotion event to audit log JSONL."""
    audit_log = Path(repo_path) / "agent_logs" / "promotion_audit.jsonl"
    audit_log.parent.mkdir(parents=True, exist_ok=True)
    event_with_timestamp = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool": tool_name,
        **event,
    }
    with open(audit_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(event_with_timestamp) + "\n")


def _compute_stats(values: List[float]) -> Dict[str, float]:
    """Compute mean, percentiles, variance for performance data."""
    if not values:
        return {}
    return {
        "mean": round(sum(values) / len(values), 3),
        "p50": round(statistics.median(values), 3),
        "p95": round(sorted(values)[max(0, int(len(values) * 0.95) - 1)], 3),
        "p99": round(sorted(values)[max(0, int(len(values) * 0.99) - 1)], 3),
        "max": round(max(values), 3),
        "min": round(min(values), 3),
        "stdev": round(statistics.stdev(values), 3) if len(values) > 1 else 0.0,
    }


def _cleanup_old_snapshots(snapshots_root: Path, keep: int = MAX_STABLE_SNAPSHOTS) -> None:
    """Remove old stable snapshots, keeping only the most recent N."""
    snapshots = sorted([d for d in snapshots_root.iterdir() if d.is_dir()], reverse=True)
    for old_snapshot in snapshots[keep:]:
        shutil.rmtree(old_snapshot)


def _build_tool_paths(repo_path: str, tool_name: str) -> ToolPaths:
    tool_root = Path(repo_path) / "ai_repo_tools" / "tools" / PILOT_CATEGORY / tool_name
    versions_root = tool_root / "versions"
    return ToolPaths(
        live_command=tool_root / "command.py",
        versions_root=versions_root,
        stable_command=versions_root / "stable" / "command.py",
        candidate_root=versions_root / "candidate",
        archived_root=versions_root / "archived",
        stable_snapshots_root=versions_root / "stable_snapshots",
    )


def _enforce_pilot_tool(tool_name: str) -> Optional[Dict]:
    if tool_name != PILOT_TOOL:
        return {
            "success": False,
            "error": "unsupported_tool",
            "detail": (
                f"v1 promotion pipeline only supports '{PILOT_TOOL}'. "
                "Generalize after pilot loop is proven."
            ),
        }
    return None


# ---------------------------------------------------------------------------
# Lifecycle init
# ---------------------------------------------------------------------------

def ensure_lifecycle(repo_path: str, tool_name: str) -> Tuple[int, Dict]:
    unsupported = _enforce_pilot_tool(tool_name)
    if unsupported:
        return 2, unsupported

    paths = _build_tool_paths(repo_path, tool_name)
    if not paths.live_command.exists():
        return 2, {
            "success": False,
            "error": "missing_live_tool",
            "target": str(paths.live_command),
        }

    (paths.versions_root / "stable").mkdir(parents=True, exist_ok=True)
    paths.candidate_root.mkdir(parents=True, exist_ok=True)
    paths.archived_root.mkdir(parents=True, exist_ok=True)
    paths.stable_snapshots_root.mkdir(parents=True, exist_ok=True)

    seeded = False
    if not paths.stable_command.exists():
        shutil.copy2(paths.live_command, paths.stable_command)
        seeded = True

    # Read deprecation info if present
    deprecation: Optional[Dict] = None
    dep_file = paths.versions_root / "deprecation.json"
    if dep_file.exists():
        try:
            deprecation = json.loads(dep_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    return 0, {
        "success": True,
        "tool": tool_name,
        "seeded_stable": seeded,
        "stable_command": str(paths.stable_command),
        "candidate_root": str(paths.candidate_root),
        "archived_root": str(paths.archived_root),
        "deprecation": deprecation,
        "summary": "Lifecycle directories ready (stable/candidate/archived/stable_snapshots).",
    }


# ---------------------------------------------------------------------------
# Version listing
# ---------------------------------------------------------------------------

def list_versions(repo_path: str, tool_name: str) -> Tuple[int, Dict]:
    code, init_payload = ensure_lifecycle(repo_path, tool_name)
    if code != 0:
        return code, init_payload

    paths = _build_tool_paths(repo_path, tool_name)
    candidates = sorted([p.name for p in paths.candidate_root.iterdir() if p.is_dir()])
    archived = sorted([p.name for p in paths.archived_root.iterdir() if p.is_dir()])
    snapshots = sorted([p.name for p in paths.stable_snapshots_root.iterdir() if p.is_dir()], reverse=True)

    deprecation = init_payload.get("deprecation")
    return 0, {
        "success": True,
        "tool": tool_name,
        "stable": "stable" if paths.stable_command.exists() else None,
        "stable_snapshots": snapshots,
        "candidates": candidates,
        "archived": archived,
        "deprecation": deprecation,
        "summary": (
            f"Found {len(candidates)} candidate(s), {len(archived)} archived, "
            f"{len(snapshots)} rollback snapshot(s)."
            + (f" [DEPRECATED: {deprecation.get('reason', '')}]" if deprecation else "")
        ),
    }


# ---------------------------------------------------------------------------
# Candidate creation
# ---------------------------------------------------------------------------

def create_candidate(repo_path: str, tool_name: str, candidate_id: Optional[str] = None) -> Tuple[int, Dict]:
    code, init_payload = ensure_lifecycle(repo_path, tool_name)
    if code != 0:
        return code, init_payload

    paths = _build_tool_paths(repo_path, tool_name)
    version_id = candidate_id or f"v{_now_stamp()}_candidate"
    candidate_dir = paths.candidate_root / version_id
    candidate_dir.mkdir(parents=True, exist_ok=False)
    candidate_command = candidate_dir / "command.py"
    shutil.copy2(paths.stable_command, candidate_command)

    # Write candidate lifecycle metadata
    lifecycle_meta = {
        "candidate_id": version_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "created_from": "stable",
        "promotion_attempts": 0,
        "final_status": "pending",
    }
    (candidate_dir / "lifecycle.json").write_text(json.dumps(lifecycle_meta, indent=2), encoding="utf-8")

    _write_audit_event(repo_path, tool_name, {
        "event": "candidate_created",
        "candidate_id": version_id,
    })

    return 0, {
        "success": True,
        "tool": tool_name,
        "candidate_id": version_id,
        "candidate_command": str(candidate_command),
        "summary": "Created candidate from stable without mutating live tool.",
    }


# ---------------------------------------------------------------------------
# Execution engine (richer metrics)
# ---------------------------------------------------------------------------

def _load_and_run(command_path: Path, repo_path: str, runs: int = 3) -> Dict:
    import importlib.util

    run_times: List[float] = []
    all_payloads: List[Dict] = []
    successes = 0
    sample_payload: Dict = {}
    errors: List[str] = []

    for i in range(runs):
        module_name = f"promotion_candidate_module_{int(time.time() * 1000)}_{i}"
        spec = importlib.util.spec_from_file_location(module_name, str(command_path))
        if not spec or not spec.loader:
            errors.append("module_spec_load_failed")
            continue
        module = importlib.util.module_from_spec(spec)

        t0 = time.perf_counter()
        try:
            spec.loader.exec_module(module)
            func = getattr(module, "cmd_trust_trend", None)
            if not callable(func):
                errors.append("missing_cmd_trust_trend")
                continue

            with redirect_stdout(io.StringIO()):
                result = func(repo_path, 20, 2)

            if isinstance(result, tuple) and len(result) == 2:
                exit_code, payload = result
            else:
                exit_code, payload = 1, {"success": False, "error": "unexpected_return_shape"}

            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            run_times.append(elapsed_ms)

            if isinstance(payload, dict):
                sample_payload = payload
                all_payloads.append(payload)

            if exit_code == 0 and isinstance(payload, dict) and payload.get("success") is True:
                successes += 1
            else:
                errors.append(f"run_failed_exit_{exit_code}")
        except Exception as exc:
            errors.append(str(exc))

    stats = _compute_stats(run_times)
    mean_ms = stats.get("mean")

    # Payload stability: flag non-determinism across runs.
    # Exclude fields that are expected to vary by design (timing, timestamps, ids).
    _EXPECTED_VARIABLE_FIELDS = {
        "elapsed_ms", "duration_ms", "elapsed", "duration",
        "timestamp", "time", "run_at", "started_at", "finished_at",
        "request_id", "trace_id",
    }
    payload_stability: Dict[str, Any] = {"all_identical": True, "differing_fields": []}
    if len(all_payloads) > 1:
        differing: List[str] = []
        for key in set().union(*(p.keys() for p in all_payloads)):
            if key in _EXPECTED_VARIABLE_FIELDS:
                continue
            values = [p.get(key) for p in all_payloads]
            try:
                if len(set(json.dumps(v, sort_keys=True) for v in values)) > 1:
                    differing.append(key)
            except TypeError:
                pass
        payload_stability["all_identical"] = len(differing) == 0
        payload_stability["differing_fields"] = differing

    return {
        "runs": runs,
        "completed_runs": len(run_times),
        "successes": successes,
        "success_rate": round((successes / float(runs)) if runs else 0.0, 3),
        "mean_ms": mean_ms,
        "performance": stats,
        "run_times_ms": [round(t, 3) for t in run_times],
        "sample_payload": sample_payload,
        "payload_stability": payload_stability,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Safety scan
# ---------------------------------------------------------------------------

def _safety_scan(command_path: Path) -> Dict:
    text = command_path.read_text(encoding="utf-8", errors="replace")
    blocked_patterns = ["os.remove(", "shutil.rmtree(", "subprocess.run(", "eval(", "exec("]
    hits = [pattern for pattern in blocked_patterns if pattern in text]
    return {
        "pass": len(hits) == 0,
        "blocked_patterns_found": hits,
    }


# ---------------------------------------------------------------------------
# Comparison + gate evaluation (config-driven)
# ---------------------------------------------------------------------------

def _compare_payloads(baseline_payload: Dict, candidate_payload: Dict) -> List[Dict]:
    """Detect field-level behavioral changes between baseline and candidate payloads."""
    changes = []
    all_keys = set(baseline_payload.keys()) | set(candidate_payload.keys())
    for key in sorted(all_keys):
        b_val = baseline_payload.get(key)
        c_val = candidate_payload.get(key)
        try:
            b_repr = json.dumps(b_val, sort_keys=True)
            c_repr = json.dumps(c_val, sort_keys=True)
        except TypeError:
            b_repr, c_repr = str(b_val), str(c_val)
        if b_repr != c_repr:
            changes.append({"field": key, "baseline": b_val, "candidate": c_val})
    return changes


def _run_gates(
    tool_name: str,
    candidate_id: str,
    baseline: Dict,
    candidate: Dict,
    safety: Dict,
    gate_config: Dict,
    repo_path: str,
) -> Tuple[Dict, List[str]]:
    """Evaluate all gates; return (checks_dict, gate_failure_reasons)."""
    correctness_floor = gate_config.get("correctness_floor", 1.0)
    max_slowdown_pct = gate_config.get("max_slowdown_pct", 5.0)
    required_keys = set(gate_config.get("required_keys", sorted(REQUIRED_PAYLOAD_KEYS)))

    baseline_mean = baseline.get("mean_ms")
    candidate_mean = candidate.get("mean_ms")
    performance_pass = False
    slowdown_pct = None
    variance_change = None

    if isinstance(baseline_mean, (int, float)) and isinstance(candidate_mean, (int, float)) and baseline_mean > 0:
        slowdown_pct = round(((candidate_mean - baseline_mean) / baseline_mean) * 100.0, 3)
        performance_pass = slowdown_pct <= max_slowdown_pct
        b_stdev = baseline.get("performance", {}).get("stdev", 0.0)
        c_stdev = candidate.get("performance", {}).get("stdev", 0.0)
        if b_stdev and b_stdev > 0:
            variance_change = round(((c_stdev - b_stdev) / b_stdev) * 100.0, 3)

    base_payload = baseline.get("sample_payload") if isinstance(baseline.get("sample_payload"), dict) else {}
    cand_payload = candidate.get("sample_payload") if isinstance(candidate.get("sample_payload"), dict) else {}
    regression_pass = required_keys.issubset(set(base_payload.keys())) and required_keys.issubset(set(cand_payload.keys()))
    behavioral_changes = _compare_payloads(base_payload, cand_payload)

    actual_correctness = candidate.get("success_rate", 0.0)
    correctness_pass = actual_correctness >= correctness_floor

    non_determinism_pass = candidate.get("payload_stability", {}).get("all_identical", True)

    checks = {
        "correctness": {
            "pass": correctness_pass,
            "floor": correctness_floor,
            "actual": actual_correctness,
        },
        "performance": {
            "pass": performance_pass,
            "max_slowdown_pct": max_slowdown_pct,
            "slowdown_pct": slowdown_pct,
            "variance_change_pct": variance_change,
        },
        "regression": {
            "pass": regression_pass,
            "required_keys": sorted(required_keys),
            "behavioral_changes": behavioral_changes,
        },
        "safety": safety,
        "non_determinism": {
            "pass": non_determinism_pass,
            "differing_fields": candidate.get("payload_stability", {}).get("differing_fields", []),
        },
    }

    failures = [
        gate for gate, result in checks.items() if not result.get("pass", False)
    ]

    # Emit per-gate audit events
    for gate, result in checks.items():
        _write_audit_event(repo_path, tool_name, {
            "event": "gate_evaluated",
            "candidate_id": candidate_id,
            "gate": gate,
            "config": {k: v for k, v in gate_config.items()},
            "result": result,
        })

    return checks, failures


# ---------------------------------------------------------------------------
# Promotion metrics tracker
# ---------------------------------------------------------------------------

def _update_promotion_metrics(repo_path: str, tool_name: str, decision: str, gate_failures: List[str]) -> None:
    metrics_path = Path(repo_path) / "agent_logs" / "promotion_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)

    metrics: Dict[str, Any] = {}
    if metrics_path.exists():
        try:
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    tools: Dict = metrics.setdefault("tools", {})
    tool_metrics: Dict = tools.setdefault(tool_name, {
        "total_candidates": 0,
        "promotions": {"succeeded": 0, "rejected": 0},
        "rejection_reasons": defaultdict(int),
    })

    tool_metrics["total_candidates"] = tool_metrics.get("total_candidates", 0) + 1
    if decision == "promote":
        tool_metrics["promotions"]["succeeded"] = tool_metrics["promotions"].get("succeeded", 0) + 1
    else:
        tool_metrics["promotions"]["rejected"] = tool_metrics["promotions"].get("rejected", 0) + 1
        reasons: Dict = tool_metrics.setdefault("rejection_reasons", {})
        for f in gate_failures:
            reasons[f] = reasons.get(f, 0) + 1

    tool_metrics["last_decision"] = decision
    tool_metrics["last_decision_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------

def rollback_tool(repo_path: str, tool_name: str, to_snapshot: Optional[str] = None, reason: str = "") -> Tuple[int, Dict]:
    code, init_payload = ensure_lifecycle(repo_path, tool_name)
    if code != 0:
        return code, init_payload

    paths = _build_tool_paths(repo_path, tool_name)
    snapshots = sorted([d for d in paths.stable_snapshots_root.iterdir() if d.is_dir()], reverse=True)
    if not snapshots:
        return 2, {"success": False, "error": "no_snapshots", "detail": "No stable snapshots available to roll back to."}

    # Pick target snapshot
    if to_snapshot:
        target_dir = paths.stable_snapshots_root / to_snapshot
        if not target_dir.is_dir():
            return 2, {"success": False, "error": "snapshot_not_found", "target": to_snapshot}
    else:
        target_dir = snapshots[0]  # most recent previous snapshot

    target_command = target_dir / "command.py"
    if not target_command.exists():
        return 2, {"success": False, "error": "snapshot_command_missing", "target": str(target_command)}

    # Take a snapshot of current before rollback
    current_snap = paths.stable_snapshots_root / f"pre_rollback_{_now_stamp()}"
    current_snap.mkdir(parents=True, exist_ok=True)
    shutil.copy2(paths.stable_command, current_snap / "command.py")

    shutil.copy2(target_command, paths.stable_command)
    shutil.copy2(target_command, paths.live_command)
    _cleanup_old_snapshots(paths.stable_snapshots_root)

    _write_audit_event(repo_path, tool_name, {
        "event": "rollback_applied",
        "rolled_back_to": target_dir.name,
        "reason": reason,
    })

    return 0, {
        "success": True,
        "tool": tool_name,
        "rolled_back_to": target_dir.name,
        "reason": reason,
        "summary": f"Rolled back {tool_name} to snapshot {target_dir.name}.",
    }


# ---------------------------------------------------------------------------
# Deprecation
# ---------------------------------------------------------------------------

def deprecate_tool(
    repo_path: str,
    tool_name: str,
    reason: str,
    successor: Optional[str] = None,
    removal_date: Optional[str] = None,
) -> Tuple[int, Dict]:
    code, init_payload = ensure_lifecycle(repo_path, tool_name)
    if code != 0:
        return code, init_payload

    paths = _build_tool_paths(repo_path, tool_name)
    dep_meta = {
        "deprecated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "reason": reason,
        "successor": successor,
        "expected_removal_date": removal_date,
    }
    dep_file = paths.versions_root / "deprecation.json"
    dep_file.write_text(json.dumps(dep_meta, indent=2), encoding="utf-8")

    _write_audit_event(repo_path, tool_name, {
        "event": "tool_deprecated",
        "reason": reason,
        "successor": successor,
        "expected_removal_date": removal_date,
    })

    return 0, {
        "success": True,
        "tool": tool_name,
        "deprecation": dep_meta,
        "summary": f"{tool_name} marked deprecated. Reason: {reason}"
        + (f" Successor: {successor}" if successor else ""),
    }


# ---------------------------------------------------------------------------
# Main promotion
# ---------------------------------------------------------------------------

def run_promotion(
    repo_path: str,
    tool_name: str,
    candidate_id: Optional[str] = None,
    runs: int = 3,
    max_slowdown_pct: float = 5.0,
) -> Tuple[int, Dict]:
    code, init_payload = ensure_lifecycle(repo_path, tool_name)
    if code != 0:
        return code, init_payload

    # Load gate config (file overrides CLI defaults per-tool)
    gate_config = _load_gate_config(repo_path, tool_name)
    # Respect CLI override for max_slowdown_pct if explicitly passed
    if max_slowdown_pct != 5.0:
        gate_config["max_slowdown_pct"] = max_slowdown_pct
    runs = gate_config.get("min_runs", runs)

    paths = _build_tool_paths(repo_path, tool_name)
    selected_candidate_id = candidate_id
    if not selected_candidate_id:
        candidates = sorted([p.name for p in paths.candidate_root.iterdir() if p.is_dir()])
        if not candidates:
            return 1, {
                "success": False,
                "error": "missing_candidate",
                "detail": "No candidate versions found. Create one with create-candidate first.",
            }
        selected_candidate_id = candidates[-1]

    candidate_command = paths.candidate_root / selected_candidate_id / "command.py"
    if not candidate_command.exists():
        return 1, {
            "success": False,
            "error": "missing_candidate_command",
            "target": str(candidate_command),
        }

    # Abort early if baseline fails (don't compare against a broken baseline)
    _write_audit_event(repo_path, tool_name, {
        "event": "promotion_started",
        "candidate_id": selected_candidate_id,
        "gate_config": gate_config,
    })

    baseline = _load_and_run(paths.stable_command, repo_path=repo_path, runs=runs)
    if baseline.get("success_rate", 0.0) < gate_config.get("correctness_floor", 1.0):
        _write_audit_event(repo_path, tool_name, {
            "event": "promotion_aborted",
            "candidate_id": selected_candidate_id,
            "reason": "baseline_failing",
            "baseline_success_rate": baseline.get("success_rate"),
        })
        return 1, {
            "success": False,
            "error": "baseline_failing",
            "detail": f"Stable baseline success_rate={baseline.get('success_rate')} below floor. Fix stable first.",
        }

    candidate = _load_and_run(candidate_command, repo_path=repo_path, runs=runs)
    safety = _safety_scan(candidate_command)

    checks, gate_failures = _run_gates(
        tool_name=tool_name,
        candidate_id=selected_candidate_id,
        baseline=baseline,
        candidate=candidate,
        safety=safety,
        gate_config=gate_config,
        repo_path=repo_path,
    )

    promote = len(gate_failures) == 0
    decision = "promote" if promote else "reject"

    # Update candidate lifecycle metadata
    lifecycle_file = paths.candidate_root / selected_candidate_id / "lifecycle.json"
    if lifecycle_file.exists():
        try:
            lc = json.loads(lifecycle_file.read_text(encoding="utf-8"))
            lc["promotion_attempts"] = lc.get("promotion_attempts", 0) + 1
            lc["final_status"] = decision
            lc["decided_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            lifecycle_file.write_text(json.dumps(lc, indent=2), encoding="utf-8")
        except Exception:
            pass

    if promote:
        # Snapshot the current stable before overwriting (versioned rollback)
        snap_id = f"snap_{_now_stamp()}"
        snap_dir = paths.stable_snapshots_root / snap_id
        snap_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(paths.stable_command, snap_dir / "command.py")
        _cleanup_old_snapshots(paths.stable_snapshots_root)

        shutil.copy2(candidate_command, paths.stable_command)
        shutil.copy2(candidate_command, paths.live_command)

        _write_audit_event(repo_path, tool_name, {
            "event": "promotion_applied",
            "candidate_id": selected_candidate_id,
            "previous_stable_snapshot": snap_id,
        })
    else:
        _write_audit_event(repo_path, tool_name, {
            "event": "promotion_rejected",
            "candidate_id": selected_candidate_id,
            "gate_failures": gate_failures,
        })

    _update_promotion_metrics(repo_path, tool_name, decision, gate_failures)

    report = {
        "schema_version": SCHEMA_VERSION,
        "tool": tool_name,
        "candidate_id": selected_candidate_id,
        "gate_config_used": gate_config,
        "baseline": {
            "runs": baseline.get("runs"),
            "success_rate": baseline.get("success_rate"),
            "mean_ms": baseline.get("mean_ms"),
            "performance": baseline.get("performance", {}),
            "payload_stability": baseline.get("payload_stability", {}),
        },
        "candidate": {
            "runs": candidate.get("runs"),
            "success_rate": candidate.get("success_rate"),
            "mean_ms": candidate.get("mean_ms"),
            "performance": candidate.get("performance", {}),
            "payload_stability": candidate.get("payload_stability", {}),
        },
        "checks": checks,
        "gate_failures": gate_failures,
        "decision": decision,
        "promoted": promote,
    }

    report_path = Path(repo_path) / "agent_logs" / f"promotion_{tool_name}_{_now_stamp()}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_with_meta = {
        **report,
        "report_path": str(report_path),
        "summary": (
            f"Promotion {'applied' if promote else 'rejected'} for {tool_name} "
            f"candidate {selected_candidate_id}."
            + (f" Gate failures: {gate_failures}" if gate_failures else "")
        ),
    }
    report_path.write_text(json.dumps(report_with_meta, indent=2), encoding="utf-8")

    _write_audit_event(repo_path, tool_name, {
        "event": "promotion_decided",
        "decision": decision,
        "candidate_id": selected_candidate_id,
        "all_gates_pass": promote,
        "gate_failures": gate_failures,
        "report_path": str(report_path),
    })

    # Exit codes: 0=promoted, 2=gate rejected, 1=error (handled above)
    exit_code = 0 if promote else 2
    return exit_code, report_with_meta
