KNOWN_SILENT_BACKGROUND_WAITS = (
    {
        "tool_name": "Bash",
        "denied_by": "peer-wait-without-liveness-exit",
        "silent_minutes": 37,
        "command": (
            "until herdr agent read w3A:p12P --source visible --lines 40 "
            "| grep -qE '^\\s*TASK-(DONE|BLOCKED)'; do sleep 90; done; "
            "herdr agent read w3A:p12P --source visible --lines 40 | grep -E '^\\s*TASK-'"
        ),
    },
    {
        "tool_name": "Bash",
        "denied_by": "peer-event-stream-outside-monitor",
        "silent_minutes": 979,
        "command": "orchestrator watch --workspace w3X --pane w3X:p8 --timeout-minutes 10",
    },
)


def known_silent_background_wait_tool_calls():
    for silent_wait in KNOWN_SILENT_BACKGROUND_WAITS:
        tool_input = {"command": silent_wait["command"]}
        if silent_wait["tool_name"] == "Bash":
            tool_input["run_in_background"] = True
        yield (
            f"{silent_wait['tool_name']}: {silent_wait['command'][:70]}",
            {"tool_name": silent_wait["tool_name"], "tool_input": tool_input},
            silent_wait["denied_by"],
        )
