import move_window_to_workspace as script


class TestBuildMoveWindowToWorkspaceCommands:
    def test_follow_mode_moves_to_workspace(self):
        commands = script.build_move_window_to_workspace_commands("follow", "3", None)
        assert "dispatch movetoworkspace 3" in commands
        assert "workspace previous" not in commands

    def test_silent_mode_returns_to_previous_workspace(self):
        commands = script.build_move_window_to_workspace_commands("silent", "3", None)
        assert "dispatch movetoworkspace 3" in commands
        assert "dispatch workspace previous" in commands

    def test_focuses_window_when_address_provided(self):
        commands = script.build_move_window_to_workspace_commands(
            "follow", "3", "0xabc"
        )
        assert "dispatch focuswindow address:0xabc" in commands

    def test_no_group_commands(self):
        commands = script.build_move_window_to_workspace_commands("follow", "3", None)
        assert "moveoutofgroup" not in commands
        assert "moveintogroup" not in commands
        assert "fullscreen" not in commands
