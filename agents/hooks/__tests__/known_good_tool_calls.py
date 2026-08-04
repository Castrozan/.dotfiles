"""Tool calls an agent makes all day, which no guard may ever deny.

Every guard here is written as a pattern over raw command text, and a pattern
widened to catch one more evasion catches ordinary work with it. The failure
is invisible from inside the rule that caused it: the guard looks correct, the
new case is denied, and the agent that hit it has no way to tell a rule from a
bug.

So the corpus lives outside any one guard and every deny-emitting hook is run
against all of it. A rule that costs a known-good call fails here, in the name
of the call it broke, rather than in a session weeks later.

Entries are whole tool calls rather than command strings because context
decides: a rebuild in the foreground is correct and the same rebuild
backgrounded is denied, and a guard can only be judged against the call the
agent actually makes.
"""

DOTFILES_REPOSITORY_PATH = "/Users/lucas.zanoni/.dotfiles"

KNOWN_GOOD_BASH_COMMANDS = (
    "git status --short",
    "git log --oneline -5",
    "git add agents/hooks/common/shell_heredoc_body.py",
    "git commit -F /tmp/commit-message.txt -- agents/hooks/common",
    "git diff --stat origin/main",
    "git worktree add .worktrees/feature -b feature",
    "grep -rn 'check_baseline\\|check-baseline' agents/__tests__/evals/*.py",
    "grep -R '__tests__/run.sh' agents",
    "rg 'make test' agents",
    "ls -la agents/hooks/__tests__/unit",
    "tree agents/hooks/nix-rebuild",
    "cat agents/hooks/common/shell_heredoc_body.py",
    "wc -l agents/hooks/common/*.py",
    "echo '__tests__/run.sh belongs to CI'",
    "pytest agents/hooks/__tests__/unit/test_shell_heredoc_body.py",
    "pytest agents/hooks/__tests__/integration/test_foreground_ci_wait_guard.py -q",
    "ruff format agents/hooks/common/shell_heredoc_body.py",
    "ruff check agents/hooks/common",
    "nixfmt home/base/codex/__tests__/hook-registration-checks.nix",
    "gh run list --commit abc123def456 --json databaseId,name,conclusion",
    "gh pr view 124 --json state,mergeStateStatus",
    "gh api repos/Castrozan/.dotfiles/actions/runs",
    "rebuild",
    "launch-command-detached-into-new-session /tmp/rebuild.log rebuild",
    "git commit -F- -- agents/hooks <<'MESSAGE'\n"
    "fix(hooks): explain what the guard forbids\n"
    "\n"
    "Running __tests__/run.sh locally stays prohibited; CI owns it.\n"
    "MESSAGE",
    "gh issue create --title perf --body-file - <<'BODY'\n"
    "pytest agents/ is CI-owned, so measure with a single file instead.\n"
    "BODY",
)

KNOWN_GOOD_BACKGROUND_BASH_COMMANDS = (
    "launch-command-detached-into-new-session /tmp/rebuild.log rebuild",
    "pytest agents/hooks/__tests__/unit/test_shell_heredoc_body.py > /tmp/out.txt 2>&1",
    "python3 -u agents/scripts/agent_session_control.py --status > /tmp/status.txt 2>&1",
    "gh run watch 30957498339 --exit-status > /tmp/ci.log 2>&1",
)

KNOWN_GOOD_FILE_WRITES = (
    f"{DOTFILES_REPOSITORY_PATH}/agents/hooks/common/shell_heredoc_body.py",
    f"{DOTFILES_REPOSITORY_PATH}/agents/hooks/__tests__/unit/test_thing.py",
    f"{DOTFILES_REPOSITORY_PATH}/home/base/claude/hooks/default.nix",
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
    for file_path in KNOWN_GOOD_FILE_WRITES:
        yield (
            f"Write: {file_path}",
            {
                "tool_name": "Write",
                "tool_input": {"file_path": file_path, "content": "value = 1\n"},
            },
        )
