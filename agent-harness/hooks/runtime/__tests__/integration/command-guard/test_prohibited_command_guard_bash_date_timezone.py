import pytest


class TestBashDateTimezoneBlocking:
    @pytest.mark.parametrize(
        "command",
        [
            "date -d '2026-08-13 23:10:05 America/Sao_Paulo' +%s",
            'date --date="2026-08-13 23:10:05 Europe/London" +%s',
            "true && date -d 'today 23:10 Etc/UTC' +%s",
            "echo \"$(date -d 'today 23:10 Etc/UTC' +%s)\"",
        ],
    )
    def test_blocks_iana_timezone_inside_date_input(
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
        assert "timezone" in message.lower()
        assert "tz=" in message.lower()

    @pytest.mark.parametrize(
        "command",
        [
            "date --iso-8601=seconds",
            "date -d 'today 23:10:05' +%s",
            "TZ=America/Sao_Paulo date -d 'today 23:10:05' +%s",
            "echo \"date -d '2026-08-13 23:10:05 America/Sao_Paulo' +%s\"",
            "echo \"wait; date -d 'today 23:10 Etc/UTC' +%s\"",
            "rg 'date -d.*America/Sao_Paulo' agent-harness",
        ],
    )
    def test_allows_valid_date_forms_and_read_only_mentions(
        self, command, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""
