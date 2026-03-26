"""Minimal benchmark comparison harness v0.

Compares two run modes (baseline vs candidate) on the same benchmark repo.
Preserves current AISH behavior. No modifications to agent or planner.

Usage:
  python harness/compare_v0.py <repo_path> <goal>

Example:
  python harness/compare_v0.py "c:\\path\\to\\Trade" "analyze structure"

Outputs:
  - harness/comparisons/<repo_name>_comparison.json
  - harness/comparisons/<repo_name>_comparison.md
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_benchmark(repo_path: str, goal: str, mode: str = "baseline", max_steps: int = 10) -> dict:
    """Run agent inspection on benchmark repo and capture logs.
    
    Args:
        repo_path: Absolute path to repo
        goal: Analysis goal
        mode: "baseline" or "candidate" (currently both identical)
        max_steps: Max agent steps
    
    Returns:
        dict with run metadata and captured log entries
    """
    log_file = "agent_logs/agent_run.log"
    
    # Capture initial log size
    initial_size = 0
    if os.path.exists(log_file):
        initial_size = os.path.getsize(log_file)
    else:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Import here to avoid circular deps
    from aish.commands import inspect_repo
    
    # Run agent
    try:
        inspect_repo(goal=goal, repo_path=repo_path, max_steps=max_steps)
    except Exception as e:
        return {
            "mode": mode,
            "success": False,
            "error": str(e),
            "entries": []
        }
    
    # Capture new log entries
    entries = []
    try:
        with open(log_file, "rb") as f:
            f.seek(initial_size)
            new_content = f.read().decode('utf-8', errors='ignore')
            for line in new_content.split('\n'):
                if line.strip() and line.startswith('{'):
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        return {
            "mode": mode,
            "success": False,
            "error": f"Log read failed: {str(e)}",
            "entries": []
        }
    
    # Extract metrics
    steps = len(entries)
    tools_used = []
    files_read = []
    
    for entry in entries:
        if "tool" in entry and entry["tool"] not in tools_used:
            tools_used.append(entry["tool"])
        if entry.get("tool") == "ai_read" and entry.get("args"):
            files_read.append(entry["args"][0])
    
    tool_sequence = [entry.get("tool", "?") for entry in entries]
    
    return {
        "mode": mode,
        "success": True,
        "repo_path": repo_path,
        "goal": goal,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "steps": steps,
        "tools_used": tools_used,
        "tool_sequence": tool_sequence,
        "files_read": files_read,
        "entries": entries
    }


def compare_runs(baseline: dict, candidate: dict) -> dict:
    """Compare two run results.
    
    Returns comparison artifact with verdict.
    """
    comparison = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "baseline": {
            "mode": baseline["mode"],
            "success": baseline["success"],
            "steps": baseline.get("steps", 0),
            "tools_used": baseline.get("tools_used", []),
            "tool_sequence": baseline.get("tool_sequence", []),
            "files_read": baseline.get("files_read", [])
        },
        "candidate": {
            "mode": candidate["mode"],
            "success": candidate["success"],
            "steps": candidate.get("steps", 0),
            "tools_used": candidate.get("tools_used", []),
            "tool_sequence": candidate.get("tool_sequence", []),
            "files_read": candidate.get("files_read", [])
        }
    }
    
    # Compute deltas
    steps_delta = candidate.get("steps", 0) - baseline.get("steps", 0)
    files_delta = len(candidate.get("files_read", [])) - len(baseline.get("files_read", []))
    
    # Determine verdict
    if not baseline["success"] or not candidate["success"]:
        verdict = "ERROR"
        detail = "One or both runs failed"
    elif baseline.get("tool_sequence") == candidate.get("tool_sequence"):
        verdict = "IDENTICAL"
        detail = "Tool sequences match; no change detected"
    elif steps_delta < 0:
        verdict = "IMPROVED"
        detail = f"Candidate used {abs(steps_delta)} fewer steps"
    elif steps_delta > 0:
        verdict = "REGRESSED"
        detail = f"Candidate used {steps_delta} more steps"
    else:
        verdict = "INCONCLUSIVE"
        detail = "Same steps but tool sequence differs"
    
    comparison["verdict"] = verdict
    comparison["detail"] = detail
    comparison["deltas"] = {
        "steps": steps_delta,
        "files_read": files_delta,
        "tools_same": baseline.get("tools_used") == candidate.get("tools_used")
    }
    
    return comparison


def generate_report(repo_name: str, comparison: dict) -> str:
    """Generate markdown comparison report."""
    b = comparison["baseline"]
    c = comparison["candidate"]
    v = comparison["verdict"]
    
    report = f"""# Benchmark Comparison Report

**Repo:** {repo_name}  
**Generated:** {comparison["timestamp"]}  
**Verdict:** `{v}`

## Summary

{comparison["detail"]}

## Baseline Run

- Steps: {b["steps"]}
- Tools used: {", ".join(b["tools_used"])}
- Files read: {len(b["files_read"])}
- Tool sequence: {" -> ".join(b["tool_sequence"][:10])}{"..." if len(b["tool_sequence"]) > 10 else ""}

## Candidate Run

- Steps: {c["steps"]}
- Tools used: {", ".join(c["tools_used"])}
- Files read: {len(c["files_read"])}
- Tool sequence: {" -> ".join(c["tool_sequence"][:10])}{"..." if len(c["tool_sequence"]) > 10 else ""}

## Comparison Summary

| Metric | Baseline | Candidate | Delta |
|--------|----------|-----------|-------|
| Steps | {b["steps"]} | {c["steps"]} | {comparison["deltas"]["steps"]:+d} |
| Files Read | {len(b["files_read"])} | {len(c["files_read"])} | {comparison["deltas"]["files_read"]:+d} |
| Tools Same | {"Y" if comparison["deltas"]["tools_same"] else "N"} | | |

### Files Read (Baseline)

{chr(10).join([f"  {i+1}. {f}" for i, f in enumerate(b["files_read"][:10])])}
{"  ..." if len(b["files_read"]) > 10 else ""}

### Files Read (Candidate)

{chr(10).join([f"  {i+1}. {f}" for i, f in enumerate(c["files_read"][:10])])}
{"  ..." if len(c["files_read"]) > 10 else ""}

## Recommendation

**Verdict: {v}**

{"Accept candidate (improvement observed)." if v == "IMPROVED" else "Review candidate (no improvement or regression detected)."}
"""
    
    return report


def main():
    if len(sys.argv) < 3:
        print("Usage: python harness/compare_v0.py <repo_path> <goal>")
        print('Example: python harness/compare_v0.py "c:\\\\path\\\\to\\\\Trade" "analyze structure"')
        sys.exit(1)
    
    repo_path = sys.argv[1]
    goal = sys.argv[2]
    repo_name = os.path.basename(repo_path)
    
    # Ensure output directory
    os.makedirs("harness/comparisons", exist_ok=True)
    
    print(f"Comparing baseline vs candidate on {repo_name}...")
    print(f"Goal: {goal}")
    print()
    
    # Run baseline (current frozen state)
    print("Running baseline...")
    baseline = run_benchmark(repo_path, goal, mode="baseline", max_steps=10)
    
    if not baseline["success"]:
        print(f"ERROR: Baseline run failed: {baseline.get('error', 'unknown')}")
        sys.exit(1)
    
    print(f"  Baseline: {baseline['steps']} steps, {len(baseline['files_read'])} files read")
    print()
    
    # Run candidate (currently identical to baseline, ready for future experiments)
    print("Running candidate...")
    candidate = run_benchmark(repo_path, goal, mode="candidate", max_steps=10)
    
    if not candidate["success"]:
        print(f"ERROR: Candidate run failed: {candidate.get('error', 'unknown')}")
        sys.exit(1)
    
    print(f"  Candidate: {candidate['steps']} steps, {len(candidate['files_read'])} files read")
    print()
    
    # Compare
    comparison = compare_runs(baseline, candidate)
    
    # Generate report
    report_md = generate_report(repo_name, comparison)
    
    # Save artifacts
    comparison_json_path = f"harness/comparisons/{repo_name}_comparison.json"
    comparison_md_path = f"harness/comparisons/{repo_name}_comparison.md"
    
    with open(comparison_json_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)
    
    with open(comparison_md_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    
    # Print report
    print("=" * 70)
    print(report_md)
    print("=" * 70)
    print()
    print(f"Artifacts saved:")
    print(f"  - {comparison_json_path}")
    print(f"  - {comparison_md_path}")
    print()
    print(f"Verdict: {comparison['verdict']}")


if __name__ == "__main__":
    main()
