DOTFILES_REPOSITORY_PATH = "/Users/lucas.zanoni/.dotfiles"

KNOWN_GOOD_BASH_COMMANDS = (
    "git status --short",
    "git log --oneline -5",
    "git add agent-harness/hooks/runtime/pre-tool-use/common/shell_heredoc_body.py",
    "git commit -F /tmp/commit-message.txt -- agent-harness/hooks/runtime/common",
    "git diff --stat origin/main",
    "git worktree add .worktrees/feature -b feature",
    "grep -rn 'check_baseline\\|check-baseline' agent-harness/quality/evaluations/suites/**/*.yaml",
    "grep -R 'repository/verification/run.sh' agents",
    "ls -la agent-harness/hooks/runtime/__tests__/unit",
    "tree agent-harness/hooks/runtime/nix-rebuild",
    "cat agent-harness/hooks/runtime/pre-tool-use/common/shell_heredoc_body.py",
    "wc -l agent-harness/hooks/runtime/common/*.py",
    "echo 'repository/verification/run.sh belongs to CI'",
    "pytest agent-harness/hooks/runtime/__tests__/unit/shell-commands/test_shell_heredoc_body.py",
    "pytest agent-harness/hooks/runtime/__tests__/integration/test_foreground_ci_wait_guard.py -q",
    "ruff format agent-harness/hooks/runtime/pre-tool-use/common/shell_heredoc_body.py",
    "ruff check agent-harness/hooks/runtime/common",
    "nixfmt agent-harness/harnesses/codex/__tests__/hook-registration-checks.nix",
    "gh run list --commit abc123def456 --json databaseId,name,conclusion",
    "gh pr view 124 --json state,mergeStateStatus",
    "gh api repos/Castrozan/.dotfiles/actions/runs",
    "rebuild",
    "xdotool mousedown 1; sleep 0.15; xdotool mouseup 1",
    "for point in '900 500' '1000 560'; do xdotool mousemove $point; sleep 0.4; done",
    "timeout 30 make test",
    "curl --retry 30 --retry-connrefused --retry-delay 1 -sf http://localhost:8080/health",
    "git commit -m 'stop agents from using sleep 30 to wait'",
    "grep -rn 'sleep [0-9]' agent-harness/hooks",
    "cat > /tmp/poll.sh <<'EOF'\nwhile true; do sleep 5; done\nEOF",
    "python3 - <<'PY'\nimport time\nfor attempt in range(3):\n    time.sleep(1)\nPY",
    "docker run -d --name keep alpine sleep infinity",
    "nvidia-smi --query-gpu=utilization.gpu --format=csv --loop=10",
    'while read -r -t 5 line; do echo "$line"; done < /tmp/events.log',
    "timeout 20 tail -f /var/log/app.log | grep -m1 READY",
    "herdr pane wait-output w4E:p6 --match READY --timeout 5000",
    "timeout 20 wait-for-event process 4030397; cat /tmp/summon.log",
    "wait-for-event file /tmp/server.log --match listening --timeout-seconds 15",
    "hypruse wait_for window_open --match Steam",
    "herdr agent wait w4E:p6 --until working --timeout 30000",
    "ci-watcher --help",
    'readlink -f "$(command -v ci-watcher)"',
    "herdr agent wait --help",
    "find agent-workflows/background-waits development/ci-watcher -type f",
    "grep -rn 'wait-for-event process' agent-harness",
    "git commit -m 'deny herdr agent wait in the foreground'",
    "launch-command-detached-into-new-session /tmp/rebuild.log rebuild",
    "git commit -F- -- agent-harness/hooks/runtime <<'MESSAGE'\n"
    "fix(hooks): explain what the guard forbids\n"
    "\n"
    "Running repository/verification/run.sh locally stays prohibited; CI owns it.\n"
    "MESSAGE",
    "gh issue create --title perf --body-file - <<'BODY'\n"
    "pytest agents/ is CI-owned, so measure with a single file instead.\n"
    "BODY",
)

KNOWN_GOOD_BACKGROUND_BASH_COMMANDS = (
    "launch-command-detached-into-new-session /tmp/rebuild.log rebuild",
    "pytest agent-harness/hooks/runtime/__tests__/unit/shell-commands/test_shell_heredoc_body.py > /tmp/out.txt 2>&1",
    "agent-session exit --print-target > /tmp/status.txt 2>&1",
    "gh run watch 30957498339 --exit-status > /tmp/ci.log 2>&1",
    "herdr agent wait w4E:p6 --until done --until blocked --timeout 3600000",
    "wait-for-event process $(pgrep -f darwin-rebuild) --timeout-seconds 3600",
    "ci-watcher 30957498339 --timeout 3600",
)

KNOWN_GOOD_MONITOR_COMMANDS = (
    "orchestrator watch --workspace w4E --pane w4E:p6 --timeout-minutes 10",
    "tail -f /var/log/app.log | grep --line-buffered ERROR",
    "wait-for-event file /tmp/rebuild.log --match 'REBUILD_EXIT='",
    "herdr pane wait-output w4E:p6 --match REVIEW-DONE --timeout 600000",
    "hypruse wait_for window_open --match Steam --timeout 30",
)

KNOWN_GOOD_FILE_WRITES = (
    f"{DOTFILES_REPOSITORY_PATH}/agent-harness/hooks/runtime/pre-tool-use/common/shell_heredoc_body.py",
    f"{DOTFILES_REPOSITORY_PATH}/agent-harness/hooks/runtime/__tests__/unit/test_thing.py",
    f"{DOTFILES_REPOSITORY_PATH}/agent-harness/hooks/integrations/claude/claude-hooks-home-manager.nix",
)


def known_good_tool_calls():
    for command in KNOWN_GOOD_BASH_COMMANDS:
        yield (
            f"Bash: {command.splitlines()[0]}",
            {"tool_name": "Bash", "tool_input": {"command": command}},
        )
    for command in KNOWN_GOOD_BACKGROUND_BASH_COMMANDS:
        yield (
            f"background Bash: {command.splitlines()[0]}",
            {
                "tool_name": "Bash",
                "tool_input": {"command": command, "run_in_background": True},
            },
        )
    for command in KNOWN_GOOD_MONITOR_COMMANDS:
        yield (
            f"Monitor: {command.splitlines()[0]}",
            {"tool_name": "Monitor", "tool_input": {"command": command}},
        )
    for file_path in KNOWN_GOOD_FILE_WRITES:
        yield (
            f"Write: {file_path}",
            {
                "tool_name": "Write",
                "tool_input": {"file_path": file_path, "content": "value = 1\n"},
            },
        )
