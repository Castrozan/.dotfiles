KNOWN_SILENT_BACKGROUND_WAITS = (
    {
        "tool_name": "Bash",
        "denied_by": "sleep-paced-loop on peer-agent",
        "silent_minutes": 170,
        "command": (
            "first=$(orchestrator heartbeat show Reviewer-w4E-p6 2>/dev/null | head -1); "
            "n=0; until { cur=$(orchestrator heartbeat show Reviewer-w4E-p6 2>/dev/null "
            '| head -1); [ "$cur" != "$first" ] && echo "$cur" '
            '| grep -qE "· (done|blocked) · "; } || [ $n -ge 240 ]; '
            "do sleep 45; n=$((n+1)); done; "
            "orchestrator heartbeat show Reviewer-w4E-p6 2>/dev/null | sed -n 1,20p"
        ),
    },
    {
        "tool_name": "Bash",
        "denied_by": "sleep-paced-loop on peer-agent",
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
    {
        "tool_name": "Bash",
        "denied_by": "forge-poll-without-cap",
        "silent_minutes": 608,
        "command": (
            "S=/tmp/scratch; "
            "until [ \"$(sed -n '/--- restart/,$p' $S/chain.log | grep -c CHAIN-DONE)\" -ge 1 ]; "
            "do sleep 30; done; "
            'until [ "$(glab api --hostname gitlab.example.com '
            "'projects/group%2Fplugin/merge_requests/118' | jq -r .state)\" = merged ]; "
            "do sleep 30; done; "
            'echo "--- restart as worker $(date +%T)" >> $S/chain.log; $S/chain.sh $S'
        ),
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
