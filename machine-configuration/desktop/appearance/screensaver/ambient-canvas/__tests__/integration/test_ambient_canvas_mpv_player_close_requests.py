import pathlib
import subprocess
import sys

import pytest

MEDIA_SCRIPTS_DIRECTORY = (
    pathlib.Path(__file__).resolve().parents[2] / "scripts" / "ambient_canvas_media"
)
pytestmark = pytest.mark.skipif(
    sys.platform != "linux", reason="Requires the Linux mpv player"
)


@pytest.fixture
def idle_mpv_player(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(MEDIA_SCRIPTS_DIRECTORY))
    import mpv_ambient_canvas_player

    socket_path = str(tmp_path / "mpv.sock")
    arguments = mpv_ambient_canvas_player.build_mpv_arguments(socket_path) + [
        "--config=no",
        "--vo=null",
        "--force-window=no",
    ]
    player = subprocess.Popen(
        arguments, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
    )
    client = mpv_ambient_canvas_player.MpvIpcClient(socket_path)
    try:
        client.connect()
        yield player, client
    finally:
        client.close()
        player.terminate()
        player.communicate(timeout=5)


@pytest.mark.parametrize(
    "close_keys",
    [
        ["CLOSE_WIN"],
        ["CLOSE_WIN"] * 5,
        ["q", "ESC", "Ctrl+w", "CLOSE_WIN"],
    ],
)
def test_close_requests_preserve_the_player_and_allow_ipc_shutdown(
    idle_mpv_player, close_keys
):
    player, client = idle_mpv_player
    for key in close_keys:
        client.send_command(["keypress", key])

    with pytest.raises(subprocess.TimeoutExpired):
        player.wait(timeout=0.2)

    client.send_command(["get_property", "idle-active"])
    for _ in range(10):
        response = client.read_event()
        assert response is not None
        if response.get("data") is True:
            break
    else:
        pytest.fail("mpv did not respond after receiving close requests")

    client.send_command(["quit"])
    assert player.wait(timeout=3) == 0
