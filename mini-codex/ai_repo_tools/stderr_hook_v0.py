import argparse
import json


def classify_stderr(stderr_text):
    text = (stderr_text or "").strip()
    lowered = text.lower()

    if not text:
        return "no_stderr"
    if "no module named" in lowered or "modulenotfounderror" in lowered:
        return "missing_dependency"
    if "no such file" in lowered or "file not found" in lowered:
        return "missing_path"
    if "permission denied" in lowered or "access is denied" in lowered:
        return "permission_error"
    if "connection refused" in lowered or "timed out" in lowered or "timeout" in lowered:
        return "connectivity_error"
    if "syntaxerror" in lowered:
        return "syntax_error"
    if "assertionerror" in lowered or "failed" in lowered:
        return "test_failure"
    return "runtime_error"


def suggest_next_step(category, command=""):
    command = command or "<command>"

    suggestions = {
        "missing_dependency": {
            "title": "Dependency likely missing",
            "suggested_action": "Check project requirements and install missing package in the active environment.",
            "suggested_command": "python -m pip install <package>",
        },
        "missing_path": {
            "title": "Path or file issue",
            "suggested_action": "Verify the working directory and target file path.",
            "suggested_command": "Get-ChildItem <path>",
        },
        "permission_error": {
            "title": "Permission blocked",
            "suggested_action": "Check file or folder permissions and whether the file is locked.",
            "suggested_command": "Test-Path <path>; Get-Acl <path>",
        },
        "connectivity_error": {
            "title": "Service/connectivity problem",
            "suggested_action": "Verify the service is running and endpoint/env config are correct.",
            "suggested_command": "Check host, port, and related environment variables",
        },
        "syntax_error": {
            "title": "Syntax issue",
            "suggested_action": "Open the failing file/line from traceback and fix syntax.",
            "suggested_command": "Run lint/typecheck or targeted test after edit",
        },
        "test_failure": {
            "title": "Test assertion failed",
            "suggested_action": "Inspect first failing assertion and compare expected vs actual behavior.",
            "suggested_command": f"Re-run failing test only for {command}",
        },
        "runtime_error": {
            "title": "Runtime failure",
            "suggested_action": "Inspect traceback root cause and run the smallest repro command.",
            "suggested_command": command,
        },
        "no_stderr": {
            "title": "No stderr available",
            "suggested_action": "Capture stderr for the failing command and retry classification.",
            "suggested_command": command,
        },
    }

    suggestion = suggestions.get(category, suggestions["runtime_error"])
    return {
        "category": category,
        "mode": "suggestion-first",
        "auto_execute": False,
        "prompt": f"I noticed a failure ({category}). Want me to run the suggested investigation step?",
        **suggestion,
    }


def build_suggestion(stderr_text, command=""):
    category = classify_stderr(stderr_text)
    suggestion = suggest_next_step(category, command=command)
    suggestion["stderr_excerpt"] = (stderr_text or "")[:300]
    return suggestion


def main():
    parser = argparse.ArgumentParser(description="Safe stderr suggestion helper (v0)")
    parser.add_argument("--command", default="", help="Command that produced stderr")
    parser.add_argument("--stderr", default="", help="Captured stderr text")
    args = parser.parse_args()

    print(json.dumps(build_suggestion(args.stderr, command=args.command)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
