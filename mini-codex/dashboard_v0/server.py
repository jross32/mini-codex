import argparse
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from collections import Counter
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from websockets.sync.server import serve as websocket_serve


COMMAND_HISTORY = []
COMMAND_LOCK = threading.Lock()
MAX_COMMAND_HISTORY = 20
STREAM_INTERVAL_SECONDS = 1.0


def _read_text(path):
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with open(path, encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    with open(path, "rb") as f:
        return f.read().decode("latin-1", errors="replace")


def _read_json(path):
    return json.loads(_read_text(path))


def _utc_now():
    return datetime.utcnow().isoformat() + "Z"


def _coerce_int(value, field_name, minimum=None):
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if minimum is not None and parsed < minimum:
        raise ValueError(f"{field_name} must be >= {minimum}")
    return parsed


def _coerce_float(value, field_name, minimum=None, maximum=None):
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number") from exc
    if minimum is not None and parsed < minimum:
        raise ValueError(f"{field_name} must be >= {minimum}")
    if maximum is not None and parsed > maximum:
        raise ValueError(f"{field_name} must be <= {maximum}")
    return parsed


def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    if value in (None, "", 0):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _parse_agent_entries(log_path):
    entries = []
    if not log_path.exists():
        return entries

    with log_path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def _split_runs(entries):
    runs = []
    current = []
    prev_repo = None
    prev_step = None

    for entry in entries:
        state = entry.get("state", {})
        repo = state.get("repo_path")
        step = state.get("steps_taken")

        starts_new = False
        if current and repo and prev_repo and repo != prev_repo:
            starts_new = True
        elif current and step is not None and prev_step is not None and step <= prev_step:
            starts_new = True

        if starts_new:
            runs.append(current)
            current = []

        current.append(entry)
        prev_repo = repo
        prev_step = step

    if current:
        runs.append(current)
    return runs


def _parse_test_select_recommendations(run):
    for entry in reversed(run):
        if entry.get("tool") != "test_select":
            continue
        raw_stdout = entry.get("result", {}).get("raw_stdout", "")
        try:
            data = json.loads(raw_stdout)
            recs = data.get("recommended_files", [])
            if recs:
                return recs
        except Exception:
            continue
    return []


def _latest_consumed_file(run):
    for entry in reversed(run):
        if entry.get("source") == "test_select_recommendation":
            args = entry.get("args") or []
            if args:
                return args[0]
    return ""


def _run_success(run):
    for entry in run:
        if entry.get("result", {}).get("success") is False:
            return False
    return True


def _score_run(run):
    tools = [e.get("tool") for e in run if e.get("tool")]
    test_select_fired = "test_select" in tools
    consumed = bool(_latest_consumed_file(run))
    bounded = len(run) <= 10
    success = _run_success(run)
    has_activity = len(run) > 0

    score = 0
    score += 10 if has_activity else 0
    score += 25 if bounded else 0
    score += 20 if test_select_fired else 0
    score += 25 if consumed else 0
    score += 20 if success else 0

    return {
        "score": max(0, min(100, score)),
        "components": {
            "run_has_activity": 10 if has_activity else 0,
            "boundedness": 25 if bounded else 0,
            "test_select_fired": 20 if test_select_fired else 0,
            "recommendation_consumed": 25 if consumed else 0,
            "no_failure": 20 if success else 0,
        },
    }


def _build_tool_activity(usage_path):
    if not usage_path.exists():
        return {
            "entry_count": 0,
            "command_counts": {},
            "tool_counts": {},
            "success_counts": {"success": 0, "failure": 0},
            "last_updated": None,
        }

    entries = _read_json(usage_path)
    command_counts = Counter()
    tool_counts = Counter()
    success_counts = {"success": 0, "failure": 0}
    last_updated = None

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        cmd = entry.get("command")
        tool = entry.get("tool")
        if cmd:
            command_counts[cmd] += 1
        if tool:
            tool_counts[tool] += 1
        if entry.get("success") is True:
            success_counts["success"] += 1
        elif entry.get("success") is False:
            success_counts["failure"] += 1

        ts = entry.get("timestamp")
        if ts and (last_updated is None or ts > last_updated):
            last_updated = ts

    return {
        "entry_count": len(entries),
        "command_counts": dict(sorted(command_counts.items())),
        "tool_counts": dict(sorted(tool_counts.items())),
        "success_counts": success_counts,
        "last_updated": last_updated,
    }


def _build_comparison_snapshot(comparisons_dir):
    if not comparisons_dir.exists():
        return None

    snapshots = []
    for file_path in sorted(comparisons_dir.glob("*.json")):
        try:
            data = _read_json(file_path)
        except Exception:
            continue

        snapshots.append(
            {
                "file": file_path.name,
                "timestamp": data.get("timestamp"),
                "verdict": data.get("verdict"),
                "baseline_steps": data.get("baseline", {}).get("steps"),
                "candidate_steps": data.get("candidate", {}).get("steps"),
                "steps_delta": data.get("deltas", {}).get("steps"),
                "files_read_delta": data.get("deltas", {}).get("files_read"),
                "tools_same": data.get("deltas", {}).get("tools_same"),
            }
        )

    snapshots.sort(key=lambda s: s.get("timestamp") or "")
    return snapshots[-1] if snapshots else None


def _average(values):
    filtered = [value for value in values if isinstance(value, (int, float))]
    if not filtered:
        return 0.0
    return sum(filtered) / len(filtered)


def _read_runtime_status(repo_root):
    path = Path(repo_root) / "agent_logs" / "orchestrator_runtime_status.json"
    if not path.exists():
        return {
            "status": "idle",
            "activity": "Idle",
            "autosaving": False,
            "last_autosave_utc": None,
        }
    try:
        data = _read_json(path)
        if not isinstance(data, dict):
            raise ValueError("invalid runtime status payload")
        return {
            "status": data.get("status", "idle"),
            "activity": data.get("activity", "Idle"),
            "autosaving": bool(data.get("autosaving", False)),
            "last_autosave_utc": data.get("last_autosave_utc"),
        }
    except Exception:
        return {
            "status": "idle",
            "activity": "Idle",
            "autosaving": False,
            "last_autosave_utc": None,
        }


def build_orchestrator_payload(repo_root):
    repo_root = Path(repo_root)
    summary_path = repo_root / "agent_logs" / "orchestrator_summary.json"
    if not summary_path.exists():
        return {
            "generated_at": _utc_now(),
            "available": False,
            "workers_spawned": 0,
            "max_total_workers": 0,
            "workers": [],
            "metrics": {
                "complete": 0,
                "running": 0,
                "failed": 0,
                "skipped": 0,
                "trusted": 0,
                "success_rate": 0.0,
                "usefulness": 0.0,
                "uncertainty_reduction": 0.0,
                "next_step_quality": 0.0,
            },
            "recent_worker_events": [],
        }

    try:
        payload = _read_json(summary_path)
    except Exception:
        return {
            "generated_at": _utc_now(),
            "available": False,
            "workers_spawned": 0,
            "max_total_workers": 0,
            "workers": [],
            "metrics": {
                "complete": 0,
                "running": 0,
                "failed": 0,
                "skipped": 0,
                "trusted": 0,
                "success_rate": 0.0,
                "usefulness": 0.0,
                "uncertainty_reduction": 0.0,
                "next_step_quality": 0.0,
            },
            "recent_worker_events": [],
        }

    workers = payload.get("workers", [])
    status_counts = Counter(worker.get("status", "unknown") for worker in workers)
    benchmarks = [worker.get("benchmark", {}) for worker in workers if isinstance(worker.get("benchmark"), dict)]
    trusted_count = sum(1 for benchmark in benchmarks if benchmark.get("trusted"))

    recent_worker_events = []
    for worker in workers[-24:]:
        recent_worker_events.append(
            {
                "worker": worker.get("worker"),
                "status": worker.get("status"),
                "steps": worker.get("steps"),
                "primary_tool": (worker.get("tools_used") or [None])[0],
                "trusted": worker.get("benchmark", {}).get("trusted"),
                "trust_score": worker.get("benchmark", {}).get("trust_score"),
            }
        )

    return {
        "generated_at": _utc_now(),
        "available": True,
        "success": payload.get("success"),
        "mode": payload.get("mode"),
        "allow_unbounded_growth": payload.get("allow_unbounded_growth"),
        "workers_spawned": payload.get("workers_spawned", len(workers)),
        "max_total_workers": payload.get("max_total_workers", 0),
        "workers": workers,
        "metrics": {
            "complete": status_counts.get("complete", 0),
            "running": status_counts.get("running", 0),
            "failed": status_counts.get("failed", 0),
            "skipped": status_counts.get("skipped", 0),
            "trusted": trusted_count,
            "success_rate": _average([benchmark.get("success_rate") for benchmark in benchmarks]),
            "usefulness": _average([benchmark.get("avg_usefulness") for benchmark in benchmarks]),
            "uncertainty_reduction": _average(
                [benchmark.get("avg_uncertainty_reduction") for benchmark in benchmarks]
            ),
            "next_step_quality": _average([benchmark.get("avg_next_step_quality") for benchmark in benchmarks]),
        },
        "runtime_status": _read_runtime_status(repo_root),
        "recent_worker_events": recent_worker_events,
    }


def _trim_command_history():
    del COMMAND_HISTORY[MAX_COMMAND_HISTORY:]


def _add_command_entry(entry):
    with COMMAND_LOCK:
        COMMAND_HISTORY.insert(0, entry)
        _trim_command_history()


def _update_command_entry(command_id, **updates):
    with COMMAND_LOCK:
        for entry in COMMAND_HISTORY:
            if entry.get("id") == command_id:
                entry.update(updates)
                break


def get_command_history():
    with COMMAND_LOCK:
        return [dict(entry) for entry in COMMAND_HISTORY]


def build_stream_payload(repo_root):
    return {
        "generated_at": _utc_now(),
        "dashboard": build_dashboard_payload(repo_root),
        "orchestrator": build_orchestrator_payload(repo_root),
        "commands": get_command_history(),
    }


def _resolve_repo_target(repo_root, repo_value):
    base = Path(repo_root).resolve()
    if not repo_value:
        return "."

    candidate = Path(repo_value)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (base / candidate).resolve()

    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise ValueError("repo must stay inside the mini-codex workspace") from exc

    if resolved == base:
        return "."
    return os.path.relpath(resolved, base)


def launch_aish_command(repo_root, request_payload):
    command_name = (request_payload.get("command") or "").strip().lower()
    if command_name not in {"map", "inspect", "orchestrate", "auto"}:
        raise ValueError("unsupported command")

    repo_arg = _resolve_repo_target(repo_root, request_payload.get("repo"))
    command = [sys.executable, "-m", "aish", command_name, "--repo", repo_arg]

    goal = (request_payload.get("goal") or "").strip()
    if command_name in {"inspect", "auto"} and not goal:
        raise ValueError("goal is required for inspect and auto")
    if goal:
        command.extend(["--goal", goal])

    iterations_value = None
    trust_threshold_value = None
    max_workers_value = None
    unbounded_value = False

    if command_name == "orchestrate":
        iterations_value = _coerce_int(request_payload.get("iterations"), "iterations", minimum=1)
        trust_threshold_value = _coerce_float(
            request_payload.get("trust_threshold"),
            "trust_threshold",
            minimum=0.0,
            maximum=1.0,
        )
        max_workers_value = _coerce_int(request_payload.get("max_workers"), "max_workers", minimum=1)
        unbounded_value = _coerce_bool(request_payload.get("unbounded"))

        if iterations_value is not None:
            command.extend(["--iterations", str(iterations_value)])
        if trust_threshold_value is not None:
            command.extend(["--trust-threshold", str(trust_threshold_value)])
        if max_workers_value is not None:
            command.extend(["--max-workers", str(max_workers_value)])
        if unbounded_value:
            command.append("--unbounded")

    command_id = str(uuid.uuid4())
    started_at = _utc_now()
    entry = {
        "id": command_id,
        "command": command_name,
        "repo": repo_arg,
        "goal": goal or None,
        "iterations": iterations_value,
        "trust_threshold": trust_threshold_value,
        "max_workers": max_workers_value,
        "unbounded": unbounded_value,
        "status": "running",
        "started_at": started_at,
        "finished_at": None,
        "exit_code": None,
        "stdout_tail": "",
        "stderr_tail": "",
    }
    _add_command_entry(entry)

    def _runner():
        process = subprocess.Popen(
            command,
            cwd=str(Path(repo_root)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        stdout, stderr = process.communicate()
        _update_command_entry(
            command_id,
            status="complete" if process.returncode == 0 else "failed",
            finished_at=_utc_now(),
            exit_code=process.returncode,
            stdout_tail=(stdout or "")[-4000:],
            stderr_tail=(stderr or "")[-4000:],
        )

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    return entry


def build_dashboard_payload(repo_root):
    repo_root = Path(repo_root)
    log_path = repo_root / "agent_logs" / "agent_run.log"
    usage_path = repo_root / "agent_logs" / "aish_usage.json"
    comparisons_dir = repo_root / "harness" / "comparisons"

    entries = _parse_agent_entries(log_path)
    runs = _split_runs(entries)
    latest_run = runs[-1] if runs else []

    latest_state = latest_run[-1].get("state", {}) if latest_run else {}
    latest_tools = [e.get("tool") for e in latest_run if e.get("tool")]
    latest_tool = latest_tools[-1] if latest_tools else None

    recommendations = _parse_test_select_recommendations(latest_run)
    top_rec = recommendations[0] if recommendations else {}
    consumed_file = _latest_consumed_file(latest_run)

    score_bundle = _score_run(latest_run) if latest_run else {"score": 0, "components": {}}

    recent_events = []
    for entry in entries[-20:]:
        state = entry.get("state", {})
        recent_events.append(
            {
                "timestamp": entry.get("timestamp"),
                "repo_path": state.get("repo_path"),
                "goal": state.get("goal"),
                "tool": entry.get("tool"),
                "success": entry.get("result", {}).get("success"),
                "step": state.get("steps_taken"),
                "source": entry.get("source"),
            }
        )

    history = []
    for run in runs[-10:]:
        state = run[-1].get("state", {}) if run else {}
        tools = [e.get("tool") for e in run if e.get("tool")]
        run_score = _score_run(run)
        history.append(
            {
                "timestamp": run[-1].get("timestamp") if run else None,
                "repo_path": state.get("repo_path"),
                "goal": state.get("goal"),
                "steps_observed": len(run),
                "status": state.get("status"),
                "test_select_fired": "test_select" in tools,
                "consumed_recommendation": bool(_latest_consumed_file(run)),
                "consumed_file": _latest_consumed_file(run),
                "score": run_score["score"],
            }
        )

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "run_now": {
            "active_repo": latest_state.get("repo_path"),
            "active_goal": latest_state.get("goal"),
            "current_tool": latest_tool,
            "status": latest_state.get("status"),
            "observed_step_count": len(latest_run),
        },
        "latest_recommendation": {
            "top_recommendation": top_rec,
            "recommendation_count": len(recommendations),
            "consumed": bool(consumed_file),
            "consumed_file": consumed_file,
        },
        "tool_activity": _build_tool_activity(usage_path),
        "effectiveness": score_bundle,
        "recent_events": recent_events,
        "recent_run_history": history,
        "comparison_snapshot": _build_comparison_snapshot(comparisons_dir),
    }


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, repo_root=None, ws_port=None, **kwargs):
        self.repo_root = repo_root
        self.ws_port = ws_port
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/dashboard":
            payload = build_dashboard_payload(self.repo_root)
            self._write_json(payload)
            return

        if parsed.path == "/api/orchestrator":
            self._write_json(build_orchestrator_payload(self.repo_root))
            return

        if parsed.path == "/api/commands":
            self._write_json({"generated_at": _utc_now(), "commands": get_command_history()})
            return

        if parsed.path == "/api/stream-config":
            self._write_json({"generated_at": _utc_now(), "ws_port": self.ws_port})
            return

        if parsed.path in {"/mission", "/mission.html"}:
            self.path = "/mission.html"
        elif parsed.path in {"/evolution", "/evolution.html"}:
            self.path = "/evolution.html"
        elif parsed.path == "/" or parsed.path == "":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/command":
            self.send_error(404, "Not found")
            return

        content_length = int(self.headers.get("Content-Length") or 0)
        raw_body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._write_json({"error": "invalid json"}, status=400)
            return

        try:
            launched = launch_aish_command(self.repo_root, payload)
        except ValueError as exc:
            self._write_json({"error": str(exc)}, status=400)
            return
        except Exception as exc:
            self._write_json({"error": f"failed to start command: {exc}"}, status=500)
            return

        self._write_json({"ok": True, "command": launched}, status=202)

    def _write_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_http_server(host, port, repo_root, ws_port):
    def handler(*args, **kwargs):
        return DashboardHandler(*args, repo_root=repo_root, ws_port=ws_port, **kwargs)

    server = ThreadingHTTPServer((host, port), handler)
    print(f"Dashboard v0 serving on http://{host}:{port}")
    print(f"Using repo root: {repo_root}")
    server.serve_forever()


def run_websocket_server(host, port, repo_root):
    def websocket_handler(connection):
        try:
            while True:
                connection.send(json.dumps(build_stream_payload(repo_root)))
                time.sleep(STREAM_INTERVAL_SECONDS)
        except Exception:
            return

    with websocket_serve(websocket_handler, host, port) as server:
        print(f"Dashboard stream serving on ws://{host}:{port}")
        server.serve_forever()


def run_servers(host, port, ws_port, repo_root):
    websocket_thread = threading.Thread(
        target=run_websocket_server,
        args=(host, ws_port, repo_root),
        daemon=True,
    )
    websocket_thread.start()
    run_http_server(host, port, repo_root, ws_port)


def main():
    parser = argparse.ArgumentParser(description="mini-codex dashboard v0 server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--ws-port", type=int)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()

    ws_port = args.ws_port or (args.port + 1)
    run_servers(args.host, args.port, ws_port, args.repo_root)


if __name__ == "__main__":
    main()
