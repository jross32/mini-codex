"""Usage tracking for AISH commands and tools.

Maintains append-only log in agent_logs/aish_usage.json
"""

import json
import os
from datetime import datetime


class UsageTracker:
    """Track command and tool usage."""

    def __init__(self, log_file="agent_logs/aish_usage.json"):
        """Initialize tracker with log file path."""
        self.log_file = log_file
        self.log_dir = os.path.dirname(log_file)

        # Ensure log directory exists
        if self.log_dir and not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir, exist_ok=True)
            except:
                pass

        # Ensure log file exists
        if not os.path.exists(self.log_file):
            try:
                with open(self.log_file, "w") as f:
                    json.dump([], f)
            except:
                pass

    def record_command(self, command_name, tool_used, success=True, duration_ms=None, error=None):
        """Record a command invocation.

        Args:
            command_name: "map", "read", "inspect", or "usage"
            tool_used: "repo_map", "ai_read", "agent_loop", etc.
            success: Whether the command succeeded
        """
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "command": command_name,
            "tool": tool_used,
            "success": success,
            "duration_ms": duration_ms,
            "error": error,
        }

        try:
            # Read existing log
            if os.path.exists(self.log_file):
                with open(self.log_file, "r") as f:
                    try:
                        log = json.load(f)
                    except:
                        log = []
            else:
                log = []

            # Append new record
            log.append(record)

            # Write back
            with open(self.log_file, "w") as f:
                json.dump(log, f, indent=2)
        except Exception:
            # Silently fail - don't break commands if logging fails
            pass

    def get_summary(self):
        """Get aggregated usage summary.

        Returns dict with counts by command and tool.
        """
        try:
            if not os.path.exists(self.log_file):
                return {}

            with open(self.log_file, "r") as f:
                try:
                    log = json.load(f)
                except:
                    log = []

            summary = {
                "commands": {},
                "tools": {},
                "failures": 0,
                "durations": {
                    "count": 0,
                    "mean_ms": None,
                    "p95_ms": None,
                },
            }

            durations = []
            for r in log:
                command = r.get("command", "unknown")
                tool = r.get("tool", "unknown")
                summary["commands"][command] = summary["commands"].get(command, 0) + 1
                summary["tools"][tool] = summary["tools"].get(tool, 0) + 1
                if not r.get("success", False):
                    summary["failures"] += 1

                duration = r.get("duration_ms")
                if isinstance(duration, (int, float)):
                    durations.append(float(duration))

            if durations:
                durations.sort()
                p95_idx = max(0, int(0.95 * (len(durations) - 1)))
                summary["durations"] = {
                    "count": len(durations),
                    "mean_ms": round(sum(durations) / len(durations), 2),
                    "p95_ms": round(durations[p95_idx], 2),
                }

            # Get timestamp of last record
            if log and isinstance(log, list) and len(log) > 0:
                summary["timestamp"] = log[-1].get("timestamp", "")

            return summary
        except Exception:
            return {}
