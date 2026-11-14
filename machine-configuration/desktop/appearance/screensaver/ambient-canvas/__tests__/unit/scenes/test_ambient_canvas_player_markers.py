from playback import player_processes

PLAYER_BINARY_PATH = "/home/user/.local/bin/player"

def test_the_running_display_is_matched_by_the_manifest_it_was_launched_with():
    assert (
        player_processes.resolve_loop_display_process_marker("/state/loops/1660x1080")
        == "/state/loops/1660x1080/loop.segments.json"
    )


def test_two_capture_geometries_produce_two_distinct_display_markers():
    assert player_processes.resolve_loop_display_process_marker(
        "/state/loops/1660x1080"
    ) != player_processes.resolve_loop_display_process_marker("/state/loops/1920x1080")


def test_stopping_the_display_matches_a_process_name_the_agent_cannot_carry():
    assert player_processes.resolve_display_process_name(PLAYER_BINARY_PATH) == "player"
