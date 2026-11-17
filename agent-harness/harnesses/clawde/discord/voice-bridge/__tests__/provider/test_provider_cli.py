import json
import os
import signal
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import pytest

from voice_provider.provider_commands import mono_clip_from_wav

CLI = Path(__file__).resolve().parents[2] / "scripts/silver_voice_cli.py"
SUBPROCESS_TIMEOUT_SECONDS = 20


def start_cli(socket_path, *arguments):
    return subprocess.Popen(
        [sys.executable, str(CLI), *arguments],
        env={**os.environ, "VOICE_BRIDGE_CONTROL_SOCKET": socket_path},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def finish_cli(process):
    stdout, stderr = process.communicate(timeout=SUBPROCESS_TIMEOUT_SECONDS)
    return process.returncode, stdout, stderr


def write_wav(path, channels, sample_rate, frames, sample_width=2):
    with wave.open(str(path), "wb") as clip:
        clip.setnchannels(channels)
        clip.setsampwidth(sample_width)
        clip.setframerate(sample_rate)
        clip.writeframes(frames)
    return path


def test_sigterm_during_play_sends_hush_and_exits_promptly(tmp_path, bridge_factory):
    bridge = bridge_factory()
    wav = write_wav(tmp_path / "clip.wav", 2, 44100, bytes(44100 * 4))
    process = start_cli(bridge.path, "play", str(wav))
    assert bridge.play_received.wait(SUBPROCESS_TIMEOUT_SECONDS)
    process.send_signal(signal.SIGTERM)
    status, _stdout, _stderr = finish_cli(process)
    assert bridge.hush_received.wait(SUBPROCESS_TIMEOUT_SECONDS)
    assert status == 128 + signal.SIGTERM
    assert {"command": "hush"} in bridge.requests


def test_play_uploads_a_stereo_wav_as_mono_with_its_own_rate(tmp_path, bridge_factory):
    bridge = bridge_factory(play_reply={"outcome": "finished"})
    wav = write_wav(tmp_path / "clip.wav", 2, 44100, bytes(44100 * 4))
    status, stdout, _stderr = finish_cli(start_cli(bridge.path, "play", str(wav)))
    assert status == 0
    assert json.loads(stdout) == {"outcome": "finished"}
    assert bridge.requests == [
        {"command": "play", "sample_rate": 44100, "byte_count": 44100 * 2}
    ]
    assert bridge.uploads == [bytes(44100 * 2)]


def test_play_outside_a_call_exits_nonzero_with_the_bridge_message(
    tmp_path, bridge_factory
):
    bridge = bridge_factory(play_reply={"error": "not_in_voice_channel"})
    wav = write_wav(tmp_path / "clip.wav", 1, 16000, bytes(3200))
    status, stdout, _stderr = finish_cli(start_cli(bridge.path, "play", str(wav)))
    assert status == 1
    assert json.loads(stdout) == {"error": "not_in_voice_channel"}


def test_play_without_a_running_bridge_exits_nonzero(tmp_path):
    wav = write_wav(tmp_path / "clip.wav", 1, 16000, bytes(3200))
    missing = os.path.join(tempfile.gettempdir(), "no-bridge-here.sock")
    status, stdout, _stderr = finish_cli(start_cli(missing, "play", str(wav)))
    assert status == 1
    assert json.loads(stdout) == {"error": "bridge_not_running"}


def test_hush_command_reaches_the_bridge(bridge_factory):
    bridge = bridge_factory()
    status, stdout, _stderr = finish_cli(start_cli(bridge.path, "hush"))
    assert status == 0
    assert json.loads(stdout) == {"outcome": "hushed"}
    assert bridge.requests == [{"command": "hush"}]


def test_capture_writes_only_the_raw_pcm_to_stdout(bridge_factory):
    pcm = bytes(range(256)) * 5
    bridge = bridge_factory(capture_bytes=pcm)
    status, stdout, stderr = finish_cli(start_cli(bridge.path, "capture"))
    assert stdout == pcm
    assert status == 1
    assert json.loads(stderr) == {"error": "bridge_closed_the_connection"}
    assert bridge.requests == [{"command": "capture"}]


def test_capture_without_a_running_bridge_keeps_stdout_empty():
    missing = os.path.join(tempfile.gettempdir(), "no-bridge-here.sock")
    status, stdout, stderr = finish_cli(start_cli(missing, "capture"))
    assert (status, stdout) == (1, b"")
    assert json.loads(stderr) == {"error": "bridge_not_running"}


@pytest.mark.parametrize(
    ("channels", "sample_width", "frames", "reason"),
    [
        (2, 1, bytes(100), "wav_must_be_16_bit_pcm_mono_or_stereo"),
        (3, 2, bytes(96), "wav_must_be_16_bit_pcm_mono_or_stereo"),
        (1, 2, b"", "wav_has_no_audio"),
    ],
)
def test_unsupported_wav_files_are_refused_with_a_reason(
    tmp_path, channels, sample_width, frames, reason
):
    wav = write_wav(tmp_path / "bad.wav", channels, 16000, frames, sample_width)
    with pytest.raises(ValueError, match=reason):
        mono_clip_from_wav(str(wav))


def test_a_file_that_is_not_a_wav_is_unreadable(tmp_path):
    path = tmp_path / "not.wav"
    path.write_bytes(b"not a wav")
    with pytest.raises(ValueError, match="wav_unreadable"):
        mono_clip_from_wav(str(path))
