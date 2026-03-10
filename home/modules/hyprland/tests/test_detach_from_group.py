import detach_from_group_and_move_to_workspace as script


class TestBuildDetachMoveMergeAndMaximizeCommands:
    def test_follow_mode_does_not_return_to_previous_workspace(self):
        commands = script.build_detach_move_merge_and_maximize_commands(
            "follow", "3", None
        )
        assert "workspace previous" not in commands
        assert "dispatch moveoutofgroup" in commands
        assert "dispatch movetoworkspace 3" in commands
        assert "dispatch fullscreen 1 set" in commands

    def test_silent_mode_returns_to_previous_workspace(self):
        commands = script.build_detach_move_merge_and_maximize_commands(
            "silent", "3", None
        )
        assert "dispatch workspace previous" in commands
        assert "dispatch fullscreenstate 1 0" in commands

    def test_focuses_window_when_address_provided(self):
        commands = script.build_detach_move_merge_and_maximize_commands(
            "follow", "3", "0xabc"
        )
        assert "dispatch focuswindow address:0xabc" in commands

    def test_merges_into_all_directions(self):
        commands = script.build_detach_move_merge_and_maximize_commands(
            "follow", "3", None
        )
        for direction in ["l", "r", "u", "d"]:
            assert f"dispatch moveintogroup {direction}" in commands
