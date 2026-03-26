import json
import os
import sys

from tools.shared import make_preview, parse_json_safe, read_text_file_with_fallback, summarize_json_value


def detect_artifact_type(path):
    norm = path.replace("\\", "/").lower()
    name = os.path.basename(norm)

    if name == "agent_run.log":
        return "agent_run_log"
    if name == "aish_usage.json":
        return "aish_usage_log"
    if norm.endswith(".json") and "/harness/comparisons/" in f"/{norm}":
        return "comparison_json"
    if norm.endswith(".json"):
        return "json"
    return "unknown"


def append_run(runs, current_run):
    if current_run:
        runs.append(current_run)


def split_agent_runs(entries):
    runs = []
    current_run = []
    prev_step = None
    prev_repo = None

    for entry in entries:
        state = entry.get("state", {})
        step = state.get("steps_taken")
        repo = state.get("repo_path")

        starts_new_run = False
        if current_run and repo and prev_repo and repo != prev_repo:
            starts_new_run = True
        elif current_run and step is not None and prev_step is not None and step <= prev_step:
            starts_new_run = True

        if starts_new_run:
            append_run(runs, current_run)
            current_run = []

        current_run.append(entry)
        prev_step = step
        prev_repo = repo

    append_run(runs, current_run)
    return runs


def summarize_agent_run_log(content):
    parsed_entries = []
    parse_errors = 0
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        data, error = parse_json_safe(line)
        if error:
            parse_errors += 1
        else:
            parsed_entries.append(data)

    if not parsed_entries:
        return {
            "parse_status": "fallback",
            "summary": "agent_run.log contained no parseable JSON entries",
            "entry_count": 0,
            "parse_error_count": parse_errors,
        }

    runs = split_agent_runs(parsed_entries)
    latest_run = runs[-1]

    tool_sequence = [entry.get("tool") for entry in latest_run if entry.get("tool")]
    latest_repo = latest_run[-1].get("state", {}).get("repo_path")
    test_select_entries = [entry for entry in latest_run if entry.get("tool") == "test_select"]
    consumed_entries = [
        entry for entry in latest_run if entry.get("source") == "test_select_recommendation"
    ]
    consumed_file = ""
    if consumed_entries:
        args = consumed_entries[0].get("args") or []
        if args:
            consumed_file = args[0]

    observed_steps = len(latest_run)
    state_steps = [
        entry.get("state", {}).get("steps_taken")
        for entry in latest_run
        if entry.get("state", {}).get("steps_taken") is not None
    ]

    return {
        "parse_status": "parsed",
        "summary": "Agent run log summary",
        "entry_count": len(parsed_entries),
        "parse_error_count": parse_errors,
        "run_count_inferred": len(runs),
        "latest_repo_path": latest_repo,
        "latest_tool_sequence": tool_sequence,
        "latest_observed_step_count": observed_steps,
        "latest_state_step_min": min(state_steps) if state_steps else None,
        "latest_state_step_max": max(state_steps) if state_steps else None,
        "test_select_fired": len(test_select_entries) > 0,
        "test_select_count": len(test_select_entries),
        "consumed_recommendation_present": len(consumed_entries) > 0,
        "consumed_recommendation_file": consumed_file,
        "boundedness_inferred": observed_steps <= 10,
    }


def summarize_comparison_artifact(content):
    data, error = parse_json_safe(content)
    if error:
        return {
            "parse_status": "fallback",
            "summary": "Comparison JSON could not be parsed",
            "parse_error": error,
        }

    if not isinstance(data, dict):
        return {
            "parse_status": "fallback",
            "summary": "Comparison artifact expected object JSON",
            "json_shape": summarize_json_value(data),
        }

    baseline = data.get("baseline", {}) if isinstance(data.get("baseline"), dict) else {}
    candidate = data.get("candidate", {}) if isinstance(data.get("candidate"), dict) else {}
    deltas = data.get("deltas", {}) if isinstance(data.get("deltas"), dict) else {}

    baseline_files = baseline.get("files_read", []) if isinstance(baseline.get("files_read"), list) else []
    candidate_files = candidate.get("files_read", []) if isinstance(candidate.get("files_read"), list) else []

    baseline_steps = baseline.get("steps")
    candidate_steps = candidate.get("steps")
    steps_delta = deltas.get("steps")
    if steps_delta is None and isinstance(baseline_steps, int) and isinstance(candidate_steps, int):
        steps_delta = candidate_steps - baseline_steps

    files_delta = deltas.get("files_read")
    if files_delta is None:
        files_delta = len(candidate_files) - len(baseline_files)

    return {
        "parse_status": "parsed",
        "summary": "Comparison artifact summary",
        "timestamp": data.get("timestamp"),
        "verdict": data.get("verdict"),
        "detail": data.get("detail"),
        "baseline_success": baseline.get("success"),
        "candidate_success": candidate.get("success"),
        "baseline_steps": baseline_steps,
        "candidate_steps": candidate_steps,
        "steps_delta": steps_delta,
        "baseline_files_read_count": len(baseline_files),
        "candidate_files_read_count": len(candidate_files),
        "files_read_delta": files_delta,
        "tools_same": deltas.get("tools_same"),
    }


def summarize_aish_usage_log(content):
    data, error = parse_json_safe(content)
    if error:
        return {
            "parse_status": "fallback",
            "summary": "AISH usage JSON could not be parsed",
            "parse_error": error,
        }

    entries = data if isinstance(data, list) else []
    command_counts = {}
    tool_counts = {}
    success_counts = {"success": 0, "failure": 0}
    last_updated = None

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        command = entry.get("command")
        tool = entry.get("tool")
        timestamp = entry.get("timestamp")
        success = entry.get("success")

        if command:
            command_counts[command] = command_counts.get(command, 0) + 1
        if tool:
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
        if success is True:
            success_counts["success"] += 1
        elif success is False:
            success_counts["failure"] += 1
        if timestamp and (last_updated is None or timestamp > last_updated):
            last_updated = timestamp

    return {
        "parse_status": "parsed",
        "summary": "AISH usage log summary",
        "entry_count": len(entries),
        "command_counts": dict(sorted(command_counts.items())),
        "tool_counts": dict(sorted(tool_counts.items())),
        "success_counts": success_counts,
        "last_updated": last_updated,
    }


def summarize_generic_json_artifact(content):
    data, error = parse_json_safe(content)
    if error:
        return {
            "parse_status": "fallback",
            "summary": "JSON artifact could not be parsed",
            "parse_error": error,
        }

    result = {
        "parse_status": "parsed",
        "summary": "JSON artifact",
        "json_shape": summarize_json_value(data),
    }
    if isinstance(data, dict):
        result["top_level_keys"] = list(data.keys())
    return result


def cmd_artifact_read(repo_path, target):
    path = os.path.join(repo_path, target)
    if not os.path.exists(path):
        print(f"ERROR: file not found: {target}", file=sys.stderr)
        return 2, {"error": "file_not_found", "target": target}

    content, encoding = read_text_file_with_fallback(path)
    artifact_type = detect_artifact_type(target)

    summary = {
        "path": target,
        "artifact_type": artifact_type,
        "line_count": len(content.splitlines()),
        "encoding": encoding,
        "preview": make_preview(content),
    }

    if artifact_type == "agent_run_log":
        summary.update(summarize_agent_run_log(content))
    elif artifact_type == "comparison_json":
        summary.update(summarize_comparison_artifact(content))
    elif artifact_type == "aish_usage_log":
        summary.update(summarize_aish_usage_log(content))
    elif artifact_type == "json":
        summary.update(summarize_generic_json_artifact(content))
    else:
        summary.update(
            {
                "parse_status": "fallback",
                "summary": "Unsupported artifact type; returning preview and metadata",
            }
        )

    print(json.dumps(summary))
    return 0, summary
