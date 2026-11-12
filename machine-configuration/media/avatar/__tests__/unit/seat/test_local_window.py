import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import local_seat
import local_window
import pytest
import remote_talk

RENDERER_CONTROLS = (
    Path(__file__).resolve().parents[3] / "renderer/renderer-controls.js"
)


def run_main(monkeypatch, *arguments):
    monkeypatch.setattr(remote_talk.sys, "argv", ["avatar-talk", *arguments])
    with pytest.raises(SystemExit) as finished:
        remote_talk.main()
    return finished.value.code


def window_steps(monkeypatch):
    steps = {"show": Mock(), "hide": Mock()}
    monkeypatch.setattr(remote_talk, "WINDOW_STEPS", steps)
    return steps


def forwarding(monkeypatch, returncode=0):
    forwarded = Mock(return_value=SimpleNamespace(returncode=returncode))
    monkeypatch.setattr(remote_talk.subprocess, "run", forwarded)
    return forwarded


@pytest.mark.parametrize("verb", ["show", "hide"])
def test_the_window_follows_a_seat_held_here(monkeypatch, verb):
    steps = window_steps(monkeypatch)
    forwarded = forwarding(monkeypatch)
    monkeypatch.setattr(local_seat, "attached", lambda: True)
    assert run_main(monkeypatch, verb) == 0
    assert forwarded.call_args.args == (["ssh", "chise", "avatar-talk", verb],)
    steps[verb].assert_called_once_with()


@pytest.mark.parametrize(("attached", "returncode"), [(False, 0), (True, 1)])
def test_the_window_stays_away_without_a_seat_or_a_conversation(
    monkeypatch, attached, returncode
):
    steps = window_steps(monkeypatch)
    forwarding(monkeypatch, returncode)
    monkeypatch.setattr(local_seat, "attached", lambda: attached)
    assert run_main(monkeypatch, "show") == returncode
    steps["show"].assert_not_called()


def test_the_tunnel_carries_the_seat_the_window_page_and_its_controls():
    forwards = [
        local_seat.TUNNEL_COMMAND[index + 1]
        for index, option in enumerate(local_seat.TUNNEL_COMMAND)
        if option == "-L"
    ]
    assert forwards == [
        "127.0.0.1:8769:127.0.0.1:8769",
        "127.0.0.1:8770:127.0.0.1:3000",
        "127.0.0.1:8765:127.0.0.1:8765",
    ]


def test_showing_replaces_an_older_window_with_a_viewer_of_the_avatar(monkeypatch):
    order = Mock()
    monkeypatch.setattr(local_seat, "end_processes_matching", order.end)
    monkeypatch.setattr(local_window.subprocess, "run", order.open)
    local_window.show()
    assert [call[0] for call in order.mock_calls] == ["end", "open"]
    assert order.end.call_args.args == (local_seat.WINDOW_PROFILE_FLAG,)
    command = order.open.call_args.args[0]
    assert "--app=http://localhost:8770/?viewer" in command
    assert local_seat.WINDOW_PROFILE_FLAG in command
    assert local_seat.WINDOW_PROFILE_FLAG != local_seat.BROWSER_PROFILE_FLAG


def test_a_tunnel_that_ends_closes_the_seat_page_and_the_window(monkeypatch):
    ended = Mock()
    monkeypatch.setattr(local_seat, "end_processes_matching", ended)
    monkeypatch.setattr(local_seat.subprocess, "run", Mock())
    local_seat.hold_tunnel_then_close_browsers()
    assert [call.args[0] for call in ended.call_args_list] == [
        local_seat.BROWSER_PROFILE_FLAG,
        local_seat.WINDOW_PROFILE_FLAG,
    ]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
@pytest.mark.parametrize(
    ("role", "announced"),
    [("renderer", ["identify", "characterChanged"]), ("viewer", ["identify"])],
)
def test_only_the_renderer_announces_its_character(role, announced):
    program = r"""
    const fs = require("node:fs");
    globalThis.BroadcastChannel = class {};
    globalThis.WebSocket = class {
      constructor() { this.sent = []; }
      send(value) { this.sent.push(JSON.parse(value)); }
    };
    (async () => {
      const source = fs.readFileSync(process.argv[1], "utf8");
      const { RendererControls } = await import(
        "data:text/javascript," + encodeURIComponent(source)
      );
      const controls = new RendererControls(
        {}, { currentCharacter: () => "vita" }, process.argv[2]
      );
      controls.connect(); controls.socket.onopen();
      console.log(JSON.stringify(controls.socket.sent));
    })();
    """
    completed = subprocess.run(
        ["node", "-e", program, str(RENDERER_CONTROLS), role],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    sent = json.loads(completed.stdout)
    assert [message["type"] for message in sent] == announced
    assert sent[0]["role"] == role
