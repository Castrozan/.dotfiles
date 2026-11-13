import json
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import audio_cli
import pytest
from pulse_audio_fake import Pulse, audio


class SeatUnderTest(ThreadingHTTPServer):
    def __init__(self):
        super().__init__(("127.0.0.1", 0), SeatHandler)
        self.requests = []
        threading.Thread(target=self.serve_forever, daemon=True).start()

    @property
    def port(self):
        return self.server_address[1]


class SeatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.requests.append(self.path)
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *arguments):
        pass


@pytest.fixture(autouse=True)
def pulse(monkeypatch):
    backend = Pulse()
    monkeypatch.setattr(audio.pulse_audio, "run", backend.call)
    monkeypatch.setattr(audio.pulse_audio, "items", backend.items)
    return backend


@pytest.fixture(autouse=True)
def runtime_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))


@pytest.fixture
def seat(monkeypatch):
    server = SeatUnderTest()
    monkeypatch.setattr(audio_cli, "SEAT_PORT", server.port)
    yield server
    server.shutdown()
    server.server_close()


@pytest.fixture
def run_cli(monkeypatch, capsys):
    def run(*arguments):
        monkeypatch.setattr(sys, "argv", ["avatar-audio", *arguments])
        audio_cli.main()
        return json.loads(capsys.readouterr().out)

    return run


@pytest.mark.parametrize(
    "arguments", [("mute", "agent", "1"), ("volume", "human", "40")]
)
def test_changing_a_level_tells_the_seat(seat, run_cli, arguments):
    run_cli("start")
    run_cli(*arguments)
    assert seat.requests == ["/levels"]


@pytest.mark.parametrize("arguments", [("start",), ("status",), ("stop",)])
def test_the_other_actions_leave_the_seat_alone(seat, run_cli, arguments):
    run_cli(*arguments)
    assert seat.requests == []


def test_no_seat_bridge_listening_does_not_fail_the_command(
    monkeypatch, run_cli, pulse
):
    with socket.socket() as unused:
        unused.bind(("127.0.0.1", 0))
        monkeypatch.setattr(audio_cli, "SEAT_PORT", unused.getsockname()[1])
    run_cli("start")
    run_cli("mute", "agent", "1")
    assert ("set-sink-mute", "AvatarMic", "1") in pulse.calls
