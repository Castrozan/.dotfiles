class TestUnknownToolsAreAllowed:
    def test_allows_unknown_tool_invocation(self, invoke_prohibited_command_guard_hook):
        result = invoke_prohibited_command_guard_hook(
            {"tool_name": "WebFetch", "tool_input": {"url": "https://example.com"}}
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_empty_payload(self, invoke_prohibited_command_guard_hook):
        result = invoke_prohibited_command_guard_hook({})
        assert result.returncode == 0
        assert result.stdout == ""


class TestInvalidInput:
    def test_exits_one_on_invalid_json(
        self, invoke_prohibited_command_guard_hook_with_raw_stdin
    ):
        result = invoke_prohibited_command_guard_hook_with_raw_stdin("not json")
        assert result.returncode == 1
