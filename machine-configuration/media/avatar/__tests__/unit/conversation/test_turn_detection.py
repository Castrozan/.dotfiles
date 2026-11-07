import json
import queue
import subprocess
import sys
import threading
from pathlib import Path
from unittest.mock import Mock

import numpy

import listener
import source_capture
import transcript_log
import turn_detector
import utterances
import whisper_features

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
FRAME = b"\xb8\x0b" * 480
SILENT_FRAME = bytes(960)


def listening_with(tmp_path, turn_finished):
    return listener.Listening(
        segments=queue.Queue(maxsize=4),
        stopping=threading.Event(),
        pending=listener.PendingSpeech(tmp_path / "marker"),
        interrupt_speaker=Mock(),
        turn_finished=turn_finished,
    )


def test_an_unfinished_turn_keeps_its_audio_for_the_next_decision():
    finished = Mock(side_effect=[False, True])
    turn = turn_detector.TurnTracker(finished)
    assert turn.add(b"first") is False
    assert turn.add(b"second") is True
    assert finished.call_args_list[1].args[0] == b"firstsecond"
    assert turn.audio == bytearray()


def test_the_turn_judged_never_exceeds_the_model_window():
    finished = Mock(return_value=False)
    turn = turn_detector.TurnTracker(finished)
    turn.add(bytes(turn_detector.TURN_BYTES))
    turn.add(b"tail")
    judged = finished.call_args.args[0]
    assert len(judged) == turn_detector.TURN_BYTES
    assert judged.endswith(b"tail")


def test_the_commands_load_without_the_listener_runtime():
    script = (
        "import sys; sys.modules['numpy'] = None; sys.modules['onnxruntime'] = None; "
        "import talk_cli, listen_cli"
    )
    paths = [str(path) for path in SCRIPTS.iterdir() if path.is_dir()] + [str(SCRIPTS)]
    result = subprocess.run(
        [sys.executable, "-I", "-c", f"import sys; sys.path[:0] = {paths!r}; {script}"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_the_model_sees_whisper_shaped_features_even_for_silence():
    features = whisper_features.log_mel_features(
        numpy.zeros(turn_detector.TURN_SAMPLES, dtype=numpy.float32)
    )
    assert features.shape == (1, 80, 800)
    assert features.dtype == numpy.float32
    assert numpy.isfinite(features).all()


def test_every_mel_band_covers_part_of_the_spectrum():
    assert whisper_features.MEL_FILTERS.shape == (201, 80)
    assert (whisper_features.MEL_FILTERS.max(axis=0) > 0).all()


def test_a_segment_carries_whether_the_speaker_finished(tmp_path):
    listening = listening_with(tmp_path, Mock(return_value=False))
    speech = source_capture.SourceSpeech("human", listening)
    for frame in [FRAME] * 30 + [SILENT_FRAME] * 40:
        speech.feed(frame)
    source, segment, turn_finished = listening.segments.get_nowait()
    assert (source, turn_finished) == ("human", False)


def test_the_transcript_records_an_unfinished_turn(tmp_path, monkeypatch):
    listening = listening_with(tmp_path, Mock())
    listening.segments.put_nowait(("human", b"pcm", False))
    monkeypatch.setattr(listener, "transcribe_when_ready", Mock(return_value="e"))
    listening.pending.begin()
    listening.pending.finish = Mock(side_effect=listening.stopping.set)
    listener.write_transcript(tmp_path / "transcript.jsonl", listening)
    entry = json.loads((tmp_path / "transcript.jsonl").read_text())
    assert entry["turn_finished"] is False


def test_an_unfinished_turn_waits_longer_for_the_rest_of_the_sentence(tmp_path):
    path = tmp_path / "transcript.jsonl"
    transcript_log.append(path, "human", "então eu acho que", turn_finished=False)
    unfinished = transcript_log.read_since(path, 0)
    assert utterances.settle_seconds_after(unfinished) == (
        utterances.UNFINISHED_TURN_SETTLE_SECONDS
    )
    transcript_log.append(path, "human", "vale a pena.")
    finished = transcript_log.read_since(path, 0)
    assert utterances.settle_seconds_after(finished) == utterances.SETTLE_SECONDS
