import monitor_streaming_pattern_validator as sut


class TestFindStreamingAntiPatternsInCommand:
    def test_returns_all_triggered_rule_names(self):
        command = "python3 worker.py | grep ERROR | sed 's/foo/bar/'"
        problems = sut.find_streaming_anti_patterns_in_command(command)
        assert "python-without-u" in problems
        assert "grep-without-line-buffered" in problems
        assert "sed-without-u" in problems

    def test_returns_empty_list_for_clean_command(self):
        command = "tail -f /var/log/app.log | grep --line-buffered ERROR"
        assert sut.find_streaming_anti_patterns_in_command(command) == []
