import pytest


class TestBashLaunchctlSubmitBlocking:
    @pytest.mark.parametrize(
        "command",
        [
            "launchctl submit -l com.clawde.steward.ci.40113115106 -o run.log -e run.log -- /bin/bash -c 'ci-watcher --repo Castrozan/.dotfiles 40113115106'",
            'launchctl remove "$label" 2>/dev/null || true\nlaunchctl submit -l "$label" -- /bin/bash validate.sh',
            "/bin/launchctl submit -l steward-rin-activate -- activate.sh",
            "sudo launchctl submit -l label -- script.sh",
        ],
    )
    def test_blocks_keep_alive_job_submission(
        self,
        command,
        invoke_prohibited_command_guard_hook,
        parse_prohibited_command_guard_system_message,
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        message = parse_prohibited_command_guard_system_message(result.stdout)
        assert "launchctl submit" in message
        assert "KeepAlive" in message

    @pytest.mark.parametrize(
        "command",
        [
            "launchctl list",
            "launchctl remove com.clawde.steward.ci.40113115106",
            "launchctl print gui/502/com.clawde.steward.ci.40113115106",
            "launchctl bootout gui/502/com.dotfiles.steward.validation.0ec61ce3",
            "grep 'launchctl submit' steward.log",
        ],
    )
    def test_allows_job_inspection_and_removal(
        self, command, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""
