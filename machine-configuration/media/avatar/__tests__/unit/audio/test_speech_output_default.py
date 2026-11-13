import http.server
import json
import shutil
import subprocess
import threading
import time
from pathlib import Path

import pytest

COMMAND = Path(__file__).resolve().parents[3] / "scripts/command.js"

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is unavailable"
)


def run_command_module(body):
    program = f"""
    const Module = require("node:module");
    const load = Module._load;
    Module._load = (request, ...rest) =>
      request === "ws" ? class {{}} : load(request, ...rest);
    const command = require({json.dumps(str(COMMAND))});
    (async () => {{
      {body}
    }})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
    """
    completed = subprocess.run(
        ["node", "-e", program], capture_output=True, text=True, check=True, timeout=30
    )
    return json.loads(completed.stdout)


class SeatHealth(http.server.BaseHTTPRequestHandler):
    reply = b'{"attached": true, "failure": null}'
    delay_seconds = 0

    def do_GET(self):
        time.sleep(self.delay_seconds)
        self.send_response(200)
        self.send_header("Content-Length", str(len(self.reply)))
        self.end_headers()
        self.wfile.write(self.reply)

    def log_message(self, *_):
        pass


@pytest.fixture
def health_url():
    handler = type("Handler", (SeatHealth,), {})
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield handler, f"http://127.0.0.1:{server.server_port}/health"
    server.shutdown()
    server.server_close()


def attached(url):
    return run_command_module(
        f"console.log(JSON.stringify(await command.seatIsAttached({json.dumps(url)})));"
    )


def test_parsing_a_speech_leaves_the_output_for_later_and_stays_synchronous():
    parsed = run_command_module(
        """
        const bare = command.parseCommand(["speak", "hello"]);
        const explicit = command.parseCommand(["speak", "hello", "happy", "mic"]);
        console.log(JSON.stringify({ bare, explicit, isPromise: bare instanceof Promise }));
        """
    )
    assert "output" not in parsed["bare"]
    assert parsed["bare"]["emotion"] == "neutral"
    assert parsed["explicit"]["output"] == "mic"
    assert parsed["isPromise"] is False


def test_a_seat_held_by_a_machine_is_attached(health_url):
    assert attached(health_url[1]) is True


@pytest.mark.parametrize(
    "reply",
    [
        b'{"attached": false, "failure": null}',
        b"{}",
        b'{"attached": "true"}',
        b"not json",
        b"",
    ],
)
def test_anything_but_attached_true_is_not_attached(health_url, reply):
    handler, url = health_url
    handler.reply = reply
    assert attached(url) is False


def test_a_bridge_that_is_not_running_is_not_attached():
    assert attached("http://127.0.0.1:9/health") is False


def test_a_bridge_that_answers_too_slowly_is_not_attached_within_the_timeout(
    health_url,
):
    handler, url = health_url
    handler.delay_seconds = 2
    started = time.monotonic()
    assert attached(url) is False
    assert time.monotonic() - started < 1.9


@pytest.mark.parametrize(
    ("seat_is_attached", "expected"), [("true", "remote"), ("false", "both")]
)
def test_a_speech_without_an_output_goes_where_the_listener_is(
    seat_is_attached, expected
):
    resolved = run_command_module(
        f"""
        const parsed = command.parseCommand(["speak", "hello"]);
        const resolved = await command.withSpeechOutput(parsed, async () => {seat_is_attached});
        console.log(JSON.stringify(resolved));
        """
    )
    assert resolved["output"] == expected
    assert resolved["text"] == "hello"


@pytest.mark.parametrize("output", ["mic", "speakers", "both", "remote"])
def test_an_explicit_output_is_always_respected_without_asking_the_seat(output):
    result = run_command_module(
        f"""
        let asked = false;
        const parsed = command.parseCommand(["speak", "hello", "neutral", "{output}"]);
        const resolved = await command.withSpeechOutput(parsed, async () => {{
          asked = true;
          return true;
        }});
        console.log(JSON.stringify({{ output: resolved.output, asked }}));
        """
    )
    assert result == {"output": output, "asked": False}


def test_only_speech_is_resolved():
    result = run_command_module(
        """
        let asked = false;
        const parsed = command.parseCommand(["status"]);
        const resolved = await command.withSpeechOutput(parsed, async () => {
          asked = true;
          return true;
        });
        console.log(JSON.stringify({ resolved, asked }));
        """
    )
    assert result == {"resolved": {"type": "getStatus"}, "asked": False}


def test_the_voice_argument_survives_the_default_output():
    resolved = run_command_module(
        """
        const parsed = command.parseCommand(["speak", "hello", "neutral", "both", "pf_dora"]);
        console.log(JSON.stringify(await command.withSpeechOutput(parsed, async () => true)));
        """
    )
    assert resolved["voice"] == "pf_dora"
    assert resolved["output"] == "both"
