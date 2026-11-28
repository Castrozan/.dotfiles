from playback import player_processes, player_service

PLAYER_BINARY_PATH = "/home/user/.local/bin/player"


def test_stopping_the_display_matches_a_process_name_the_agent_cannot_carry():
    assert player_processes.resolve_display_process_name(PLAYER_BINARY_PATH) == "player"


def test_a_loop_replacement_restarts_the_dedicated_player_service_on_each_platform():
    linux_command = player_service.build_player_restart_command("linux", 1000)
    darwin_command = player_service.build_player_restart_command("darwin", 501)
    assert linux_command[1:] == ["--user", "restart", "ambient-canvas-player.service"]
    assert darwin_command[1:] == [
        "kickstart",
        "-k",
        "gui/501/com.dotfiles.ambient-canvas-player",
    ]
