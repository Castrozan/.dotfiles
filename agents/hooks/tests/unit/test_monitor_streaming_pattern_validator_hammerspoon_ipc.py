import monitor_streaming_pattern_validator as sut

HAMMERSPOON_IPC_RULE_NAME = "hammerspoon-ipc-blocks-without-timeout"


class TestHammerspoonIpcWithoutTimeout:
    def test_flags_bare_hs_eval_call(self):
        triggered = sut.find_hang_anti_patterns_in_command('hs -c "return 1"')
        assert HAMMERSPOON_IPC_RULE_NAME in triggered

    def test_flags_absolute_path_hs_eval_call(self):
        triggered = sut.find_hang_anti_patterns_in_command(
            '/opt/homebrew/bin/hs -c "hs.reload()"'
        )
        assert HAMMERSPOON_IPC_RULE_NAME in triggered

    def test_allows_hs_eval_wrapped_in_gtimeout(self):
        triggered = sut.find_hang_anti_patterns_in_command(
            'gtimeout 8 hs -c "return 1"'
        )
        assert HAMMERSPOON_IPC_RULE_NAME not in triggered

    def test_allows_hs_eval_wrapped_in_timeout(self):
        triggered = sut.find_hang_anti_patterns_in_command('timeout 8 hs -c "return 1"')
        assert HAMMERSPOON_IPC_RULE_NAME not in triggered

    def test_ignores_hs_without_eval_flag(self):
        assert sut.find_hang_anti_patterns_in_command("hs --version") == []

    def test_ignores_unrelated_command_containing_hs_substring(self):
        assert sut.find_hang_anti_patterns_in_command("ssh remotehost uptime") == []
