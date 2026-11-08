import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import conversation_state
import listener_session
import pytest
import start
import conversation_effects
import talk_cli
import utterances
from conversation_state import ConversationPhase

AVATAR_DIRECTORY = Path(__file__).resolve().parents[2]
requires_node = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is unavailable"
)


@requires_node
def test_renderer_controls_answer_character_requests_with_their_identity():
    program = r"""
    const fs = require("node:fs");
    class Socket { constructor() { this.sent = []; } send(value) { this.sent.push(JSON.parse(value)); } }
    globalThis.BroadcastChannel = class {};
    globalThis.WebSocket = Socket;
    (async () => {
      const source = fs.readFileSync(process.argv[1], "utf8");
      const { RendererControls } = await import("data:text/javascript," + encodeURIComponent(source));
      const controls = new RendererControls({}, {
        showCharacter: async name => { if (name !== "vita") throw new Error("Unknown character"); },
      });
      controls.connect();
      await controls.handlers.setCharacter({ name: "vita", id: "known" });
      await controls.handlers.setCharacter({ name: "nobody", id: "unknown" });
      console.log(JSON.stringify(controls.socket.sent));
    })().catch(error => { console.error(error); process.exitCode = 1; });
    """
    source = AVATAR_DIRECTORY / "renderer/renderer-controls.js"
    completed = subprocess.run(
        ["node", "-e", program, str(source)], capture_output=True, text=True, check=True
    )
    assert json.loads(completed.stdout) == [
        {"type": "characterChanged", "name": "vita", "id": "known"},
        {"type": "characterError", "message": "Unknown character", "id": "unknown"},
    ]


@requires_node
def test_renderer_announces_its_character_on_every_connection():
    program = r"""
    const fs = require("node:fs");
    class Socket { constructor() { this.sent = []; } send(value) { this.sent.push(JSON.parse(value)); } }
    globalThis.BroadcastChannel = class {};
    globalThis.WebSocket = Socket;
    (async () => {
      const source = fs.readFileSync(process.argv[1], "utf8");
      const { RendererControls } = await import("data:text/javascript," + encodeURIComponent(source));
      const controls = new RendererControls({}, { currentCharacter: () => "vita" });
      controls.connect();
      controls.socket.onopen();
      console.log(JSON.stringify(controls.socket.sent));
    })().catch(error => { console.error(error); process.exitCode = 1; });
    """
    source = AVATAR_DIRECTORY / "renderer/renderer-controls.js"
    completed = subprocess.run(
        ["node", "-e", program, str(source)], capture_output=True, text=True, check=True
    )
    assert json.loads(completed.stdout) == [
        {"type": "identify", "role": "renderer"},
        {"type": "characterChanged", "name": "vita"},
    ]


def run_talk(monkeypatch, directory, *arguments):
    monkeypatch.setattr(sys, "argv", ["avatar-talk", *arguments])
    monkeypatch.setattr(talk_cli.listener, "runtime_directory", lambda: directory)
    talk_cli.main()


def fake_cold_open(tmp_path, monkeypatch):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.CLOSED
    )
    monkeypatch.setattr(listener_session, "listening", lambda: False)
    monkeypatch.setattr(listener_session, "begin_listening", Mock())
    monkeypatch.setattr(start, "bring_up", Mock())
    utterances.remember(tmp_path, 0)


def test_opening_chooses_the_character_without_presenting_the_window(
    tmp_path, monkeypatch
):
    fake_cold_open(tmp_path, monkeypatch)
    runner = Mock()
    monkeypatch.setattr(conversation_effects.subprocess, "run", runner)
    conversation_effects.open_conversation(
        argparse.Namespace(language="pt", character="vita"), tmp_path
    )
    commands = [call.args[0] for call in runner.call_args_list]
    assert commands[0] == ["avatar-command", "character", "vita"]
    assert ["avatar-command", "presence", "shown"] not in commands


def test_opening_without_a_choice_keeps_the_current_character(tmp_path, monkeypatch):
    fake_cold_open(tmp_path, monkeypatch)
    runner = Mock()
    monkeypatch.setattr(conversation_effects.subprocess, "run", runner)
    conversation_effects.open_conversation(
        argparse.Namespace(language="pt", character=None), tmp_path
    )
    assert "character" not in [
        word for call in runner.call_args_list for word in call.args[0]
    ]


def test_opening_an_open_conversation_still_switches_the_character(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.OPEN
    )
    runner = Mock()
    monkeypatch.setattr(conversation_effects.subprocess, "run", runner)
    run_talk(monkeypatch, tmp_path, "open", "--character", "vivi")
    assert runner.call_args_list[0].args[0] == ["avatar-command", "character", "vivi"]


def test_a_refused_character_closes_a_cold_open(tmp_path, monkeypatch):
    fake_cold_open(tmp_path, monkeypatch)
    monkeypatch.setattr(
        conversation_effects.subprocess,
        "run",
        Mock(side_effect=subprocess.CalledProcessError(1, "avatar-command")),
    )
    close = Mock()
    monkeypatch.setattr(conversation_effects, "close_conversation", close)
    with pytest.raises(subprocess.CalledProcessError):
        conversation_effects.open_conversation(
            argparse.Namespace(language=None, character="nobody"), tmp_path
        )
    close.assert_called_once()
