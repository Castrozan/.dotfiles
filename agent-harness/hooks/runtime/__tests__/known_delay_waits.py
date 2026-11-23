FOREGROUND = ("Bash", False)
BACKGROUND = ("Bash", True)
MONITOR = ("Monitor", False)

KNOWN_DELAY_WAITS = (
    ("sleep 70; echo window-cleared", FOREGROUND, "fixed-delay", "unknown"),
    (
        "until grep -q 'REBUILD_EXIT=' \"$L\"; do sleep 3; done; grep 'REBUILD_EXIT=' \"$L\"",
        MONITOR,
        "sleep-paced-loop",
        "file-content",
    ),
    (
        "until ! pgrep -f darwin-rebuild >/dev/null; do sleep 15; done; echo rebuild-exited",
        BACKGROUND,
        "sleep-paced-loop",
        "process-exit",
    ),
    (
        "for attempt in $(seq 1 45); do "
        "verdict=$(gh run view 30957498339 --json conclusion --jq .conclusion); "
        '[ -n "$verdict" ] && break; sleep 20; done; echo "verdict: $verdict"',
        BACKGROUND,
        "sleep-paced-loop",
        "ci-run",
    ),
    (
        "gh pr merge 211 --merge 2>&1 | tail -2; sleep 20; "
        "gh run list --branch main --limit 2 --json databaseId,status",
        FOREGROUND,
        "fixed-delay",
        "ci-run",
    ),
    (
        "sleep 40; a2a status 0c7f 2>&1 | head -12",
        FOREGROUND,
        "fixed-delay",
        "peer-agent",
    ),
    (
        "first=$(orchestrator heartbeat show Reviewer-w4E-p6 2>/dev/null | head -1); "
        'until [ "$(orchestrator heartbeat show Reviewer-w4E-p6 | head -1)" != "$first" ] '
        "|| ! herdr pane get w4E:p6 >/dev/null 2>&1; do sleep 45; done",
        MONITOR,
        "sleep-paced-loop",
        "peer-agent",
    ),
    (
        "sleep 30; herdr pane read w1:p2 --lines 12 2>&1 | tail -12",
        FOREGROUND,
        "fixed-delay",
        "pane-output",
    ),
    (
        "systemctl --user stop app.service; sleep 2; "
        "nvidia-smi --query-gpu=memory.used --format=csv,noheader",
        FOREGROUND,
        "fixed-delay",
        "service-state",
    ),
    (
        "nohup python3 -m http.server 8731 --bind 127.0.0.1 > /tmp/serve.log 2>&1 &\n"
        "sleep 1; curl -sI http://127.0.0.1:8731/ | head -1",
        FOREGROUND,
        "fixed-delay",
        "local-endpoint",
    ),
    (
        "for i in $(seq 120); do ss -ltn | rg -q ':8767 ' && break; sleep .25; done",
        FOREGROUND,
        "sleep-paced-loop",
        "local-endpoint",
    ),
    (
        "timeout 60 bash -c 'until curl -sf http://localhost:8093/health; do sleep 1; done'",
        FOREGROUND,
        "sleep-paced-loop",
        "local-endpoint",
    ),
    (
        'python3 -c "import time;time.sleep(8)"; echo continuing',
        FOREGROUND,
        "fixed-delay",
        "unknown",
    ),
    (
        "for i in 1 2 3 4; do herdr pane send-keys w1:p2 shift+tab; "
        'python3 -c "import time;time.sleep(1.5)"; '
        "herdr agent read w1:p2 --source visible --lines 3; done",
        FOREGROUND,
        "sleep-paced-loop",
        "peer-agent",
    ),
    (
        "sleep 60; cat /tmp/claude-1000/project/session/tasks/b1x2y3z4.output",
        FOREGROUND,
        "fixed-delay",
        "background-task-output",
    ),
    (
        "steam steam://nav/games/details/1 >/dev/null 2>&1 & sleep 6; "
        "hypruse screenshot --scale 0.5",
        FOREGROUND,
        "fixed-delay",
        "desktop-window",
    ),
    (
        "chrome-devtools click 4 3_43 >/dev/null 2>&1; sleep 2; "
        "chrome-devtools take_snapshot 4 | grep StaticText",
        FOREGROUND,
        "fixed-delay",
        "browser-page",
    ),
    (
        'while sleep 0.5; do echo "$(date +%T) $(grep -c Modesetting /tmp/x.log)"; '
        "done > /tmp/timeline.log",
        BACKGROUND,
        "sleep-paced-loop",
        "file-content",
    ),
    (
        "until [ ! -e ~/.local/share/app/game.lock ]; do sleep 5; done; echo free",
        FOREGROUND,
        "sleep-paced-loop",
        "file-content",
    ),
    (
        "for i in $(seq 1 60); do s=$(glab mr view 4 -F json | jq -r .state); "
        '[ "$s" != opened ] && break; sleep 30; done',
        FOREGROUND,
        "sleep-paced-loop",
        "forge-merge-request",
    ),
    (
        'until [ "$(date +%H%M%S)" -ge 191705 ]; do sleep 3; done',
        FOREGROUND,
        "sleep-paced-loop",
        "unknown",
    ),
    ("watch -n 5 'gh run list --limit 3'", BACKGROUND, "sleep-paced-loop", "ci-run"),
)


def known_delay_wait_tool_calls():
    for command, (
        tool_name,
        runs_in_background,
    ), rule_name, target_name in KNOWN_DELAY_WAITS:
        tool_input = {"command": command}
        if runs_in_background:
            tool_input["run_in_background"] = True
        yield (
            f"{tool_name}{'-bg' if runs_in_background else ''}: {command[:60]}",
            {"tool_name": tool_name, "tool_input": tool_input},
            f"{rule_name} on {target_name}",
        )
