import queue
import threading
import time
from unittest.mock import Mock

import listener
import pytest
import transcript_log
import utterances


def listening_with_open_queue(tmp_path):
    return listener.Listening(
        segments=queue.Queue(),
        stopping=threading.Event(),
        pending=listener.PendingSpeech(tmp_path / listener.SPEECH_IN_PROGRESS_MARKER),
        interrupt_speaker=Mock(),
    )


def test_a_conversation_closing_during_the_settle_wait_returns_promptly(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(utterances, "UNFINISHED_SPEECH_LIMIT_SECONDS", 1.5)
    transcript_log.append(tmp_path / "transcript.jsonl", "human", "oi")
    (tmp_path / listener.SPEECH_IN_PROGRESS_MARKER).touch()
    answers = iter([True, False])
    started = time.monotonic()
    utterance = utterances.next_utterance(tmp_path, 0, lambda: next(answers, False))
    assert time.monotonic() - started < 1
    assert utterance == "oi"


def test_a_second_consumer_is_refused_while_the_first_holds_the_cursor(tmp_path):
    with utterances.exclusive_consumer(tmp_path):
        with pytest.raises(utterances.ConversationBusy, match="already listening"):
            with utterances.exclusive_consumer(tmp_path):
                pass
    with utterances.exclusive_consumer(tmp_path):
        pass


def test_the_consumer_lock_creates_a_private_runtime_directory(tmp_path):
    runtime = tmp_path / "avatar"
    with utterances.exclusive_consumer(runtime):
        assert runtime.stat().st_mode & 0o777 == 0o700


def test_the_marker_is_cleared_when_the_writer_exits_with_segments_queued(tmp_path):
    listening = listening_with_open_queue(tmp_path)
    listening.pending.begin()
    listening.segments.put_nowait(("human", b"waiting", True))
    listening.stopping.set()
    listener.write_transcript(tmp_path / "transcript.jsonl", listening)
    assert listening.segments.qsize() == 1
    assert not (tmp_path / listener.SPEECH_IN_PROGRESS_MARKER).exists()


def test_the_settle_wait_asks_whether_the_conversation_is_open_about_once_a_second(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(utterances, "UNFINISHED_SPEECH_LIMIT_SECONDS", 1.5)
    monkeypatch.setattr(utterances, "POLL_SECONDS", 0.01)
    transcript_log.append(tmp_path / "transcript.jsonl", "human", "oi")
    (tmp_path / listener.SPEECH_IN_PROGRESS_MARKER).touch()
    still_open = Mock(return_value=True)
    utterances.wait_for_finished_speech(
        tmp_path,
        transcript_log.read_since(tmp_path / "transcript.jsonl", 0),
        still_open,
    )
    assert still_open.call_count <= 3
