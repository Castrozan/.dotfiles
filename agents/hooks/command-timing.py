#!/usr/bin/env python3
"""command-timing.py - Track command execution times for debugging slow operations."""

import json
import os
import sys
import time
from pathlib import Path

# Track timing data in a simple file
TIMING_LOG = Path.home() / ".claude" / "logs" / "command-timing.jsonl"


def ensure_log_dir():
    """Ensure the log directory exists."""
    TIMING_LOG.parent.mkdir(parents=True, exist_ok=True)


def log_timing(data: dict):
    """Append timing data to log file."""
    ensure_log_dir()
    try:
        with open(TIMING_LOG, "a") as f:
            f.write(json.dumps(data) + "\n")
    except IOError:
        pass


def get_slow_command_stats() -> dict:
    """Get statistics about slow commands from recent history."""
    if not TIMING_LOG.exists():
        return {}

    try:
        slow_commands = []
        with open(TIMING_LOG) as f:
            lines = f.readlines()[-100:]  # Last 100 entries
            for line in lines:
                try:
                    entry = json.loads(line)
                    if entry.get("duration_ms", 0) > 5000:  # > 5 seconds
                        slow_commands.append(entry)
                except json.JSONDecodeError:
                    continue

        return {
            "slow_count": len(slow_commands),
            "slowest": max((c.get("duration_ms", 0) for c in slow_commands), default=0)
        }
    except IOError:
        return {}


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    hook_event = data.get("hook_event_name", "")
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    session_id = data.get("session_id", "unknown")

    # PreToolUse: Record start time
    if hook_event == "PreToolUse":
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            # Store start time in environment-like mechanism via output
            timing_data = {
                "event": "start",
                "session_id": session_id,
                "tool": tool_name,
                "command": command[:100],  # Truncate for log
                "timestamp": time.time()
            }
            log_timing(timing_data)

    # PostToolUse: Calculate duration and warn if slow
    elif hook_event == "PostToolUse":
        if tool_name == "Bash":
            # Find matching start entry
            if TIMING_LOG.exists():
                try:
                    with open(TIMING_LOG) as f:
                        lines = f.readlines()

                    # Find the last start entry for this session
                    start_time = None
                    command = tool_input.get("command", "")[:100]

                    for line in reversed(lines[-20:]):  # Check last 20
                        try:
                            entry = json.loads(line)
                            if (entry.get("event") == "start" and
                                entry.get("session_id") == session_id and
                                entry.get("command") == command):
                                start_time = entry.get("timestamp")
                                break
                        except json.JSONDecodeError:
                            continue

                    if start_time:
                        duration_ms = int((time.time() - start_time) * 1000)

                        # Log completion
                        timing_data = {
                            "event": "complete",
                            "session_id": session_id,
                            "tool": tool_name,
                            "command": command,
                            "duration_ms": duration_ms,
                            "timestamp": time.time()
                        }
                        log_timing(timing_data)

                        # Warn about slow commands
                        if duration_ms > 30000:  # > 30 seconds
                            stats = get_slow_command_stats()
                            message = (
                                f"TIMING: Command took {duration_ms/1000:.1f}s\n"
                                f"Consider using tmux for long-running processes."
                            )
                            if stats.get("slow_count", 0) > 5:
                                message += (
                                    f"\nNote: {stats['slow_count']} slow commands in recent history."
                                )

                            output = {
                                "continue": True,
                                "systemMessage": message
                            }
                            print(json.dumps(output))

                except IOError:
                    pass

    sys.exit(0)


if __name__ == "__main__":
    main()
