import json
import shutil
import subprocess
from pathlib import Path

import pytest
import seat_page

VOICE_DELAY = (
    Path(__file__).resolve().parents[4]
    / "scripts/conversation/remote_seat/page/voice-delay.js"
)

REPORTING = r"""
const [queues, outputs] = process.argv.slice(1, 3).map(JSON.parse);
globalThis.WebSocket = { OPEN: 1 };
import(process.argv.at(-1)).then(({ reportVoiceDelay }) => {
  const socket = { readyState: 0, sent: [], send(message) { this.sent.push(JSON.parse(message)); } };
  const voice = { port: {} };
  reportVoiceDelay(voice, outputs, socket);
  voice.port.onmessage({ data: { queuedSeconds: 0.5 } });
  socket.readyState = 1;
  socket.onopen();
  for (const queuedSeconds of queues) voice.port.onmessage({ data: { queuedSeconds } });
  console.log(JSON.stringify(socket.sent));
});
"""

HEADSET = {"baseLatency": 0.01, "outputLatency": 0.2}
CALL = {"baseLatency": 0.01, "outputLatency": 0}

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is unavailable"
)


def report(queues, outputs):
    completed = subprocess.run(
        [
            "node",
            "--input-type=module",
            "-e",
            REPORTING,
            json.dumps(queues),
            json.dumps(outputs),
            VOICE_DELAY.as_uri(),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return json.loads(completed.stdout)


def test_each_display_copy_learns_the_queue_plus_its_own_output_delay():
    sent = report([0.12], {"viewer": HEADSET, "stage": CALL})
    assert sent[0] == {"type": "identify", "role": "seat"}
    assert sent[1]["type"] == "voiceDelay"
    assert sent[1]["viewer"] == pytest.approx(0.33)
    assert sent[1]["stage"] == pytest.approx(0.13)
    assert len(sent) == 2


def test_only_a_change_the_eye_could_see_is_reported_again():
    sent = report([0.12, 0.13, 0.14, 0.3, 0.3], {"viewer": HEADSET})
    assert [message["viewer"] for message in sent[1:]] == pytest.approx([0.33, 0.51])


def test_a_context_that_cannot_tell_its_output_latency_counts_its_base_alone():
    sent = report([0], {"viewer": {"baseLatency": 0.02}})
    assert sent[1]["viewer"] == pytest.approx(0.02)


def test_the_seat_page_serves_its_voice_delay_module(tmp_path):
    files = seat_page.seat_page_files(tmp_path)
    assert files["/voice-delay.js"] == (tmp_path / "voice-delay.js", seat_page.JAVASCRIPT)
