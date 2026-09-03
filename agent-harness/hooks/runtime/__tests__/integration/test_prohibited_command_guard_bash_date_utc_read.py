import pytest


class TestBashDateUtcClockReadBlocking:
    @pytest.mark.parametrize(
        "command",
        [
            "date -u",
            "date --utc '+%Y-%m-%d %H:%M'",
            "date +%H:%M -u",
            "TZ=UTC date",
            "TZ=\"Etc/UTC\" date '+%F %T'",
            "env TZ=UTC date +%s",
            "true && TZ=GMT date",
            'echo "$(date -u +%FT%TZ)"',
        ],
    )
    def test_blocks_reading_the_clock_in_utc(
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
        assert "utc" in message.lower()
        assert "Run plain date instead" in message

    @pytest.mark.parametrize(
        "command",
        [
            "date",
            "date '+%Y-%m-%d %H:%M %Z'",
            "date +%s",
            "TZ=America/Sao_Paulo date",
            "date -u -d '2026-09-02T18:53:47Z' +%s",
            "TZ=UTC date -j -f '%Y-%m-%dT%H:%M:%SZ' '2026-09-02T18:53:47Z' +%s",
            "TZ=UTC date -d @1756843200",
            "date -u -r 1756843200",
            'echo "date -u"',
            'echo "wait; TZ=UTC date"',
            "rg 'date -u' agent-harness",
            "git log --date=iso-strict -1",
            "cat <<'EOF'\ndate -u\nEOF",
        ],
    )
    def test_allows_local_reads_conversions_and_read_only_mentions(
        self, command, invoke_prohibited_command_guard_hook
    ):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "Bash", "tool_input": {"command": command}}
        )
        assert result.returncode == 0
        assert result.stdout == ""
