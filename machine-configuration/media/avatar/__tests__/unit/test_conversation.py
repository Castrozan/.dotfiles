import argparse
import json
import queue
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import desktop_window
import listener
import listen_cli
import start
import talk_cli
import transcript_log
import utterances

FRAME = b"\xb8\x0b" * 480
SILENT_FRAME = bytes(960)


def always_open():
    return True


def listening_with(tmp_path, interrupt=None):
    return listener.Listening(
        segments=queue.Queue(maxsize=1),
        stopping=threading.Event(),
        pending=listener.PendingSpeech(tmp_path / "marker"),
        interrupt_speaker=interrupt or Mock(),
    )


def test_a_pending_utterance_is_marked_until_every_part_finished(tmp_path):
    pending = listener.PendingSpeech(tmp_path / "marker")
    pending.begin()
    pending.begin()
    pending.finish()
    assert (tmp_path / "marker").exists()
    pending.finish()
    assert not (tmp_path / "marker").exists()


def test_a_stale_marker_from_a_killed_listener_is_cleared(tmp_path):
    (tmp_path / "marker").touch()
    listener.PendingSpeech(tmp_path / "marker")
    assert not (tmp_path / "marker").exists()


def test_sustained_speech_interrupts_the_speaker_once_per_segment(tmp_path):
    listening = listening_with(tmp_path)
    speech = listener.SourceSpeech("human", listening)
    for _ in range(40):
        speech.feed(FRAME)
    listening.interrupt_speaker.assert_called_once()


def test_a_short_noise_never_interrupts_and_leaves_nothing_pending(tmp_path):
    listening = listening_with(tmp_path)
    speech = listener.SourceSpeech("human", listening)
    for frame in [FRAME] * 3 + [SILENT_FRAME] * 40:
        speech.feed(frame)
    listening.interrupt_speaker.assert_not_called()
    assert not (tmp_path / "marker").exists()


def test_a_finished_segment_stays_pending_until_it_is_transcribed(tmp_path):
    listening = listening_with(tmp_path)
    speech = listener.SourceSpeech("human", listening)
    for frame in [FRAME] * 30 + [SILENT_FRAME] * 40:
        speech.feed(frame)
    assert listening.segments.qsize() == 1
    assert (tmp_path / "marker").exists()


def test_a_segment_dropped_for_a_full_queue_is_not_left_pending(tmp_path):
    listening = listening_with(tmp_path)
    listening.segments.put_nowait(("human", b"waiting"))
    speech = listener.SourceSpeech("human", listening)
    for frame in [FRAME] * 30 + [SILENT_FRAME] * 40:
        speech.feed(frame)
    assert not (tmp_path / "marker").exists()


def test_capture_lost_mid_speech_leaves_nothing_pending(tmp_path):
    listening = listening_with(tmp_path)
    speech = listener.SourceSpeech("human", listening)
    speech.feed(FRAME)
    speech.abandon()
    assert not (tmp_path / "marker").exists()


def test_transcription_failure_still_releases_the_pending_marker(tmp_path, monkeypatch):
    listening = listening_with(tmp_path)
    listening.pending.begin()
    listening.segments.put_nowait(("human", b"pcm"))
    monkeypatch.setattr(
        listener, "transcribe_when_ready", Mock(side_effect=TimeoutError)
    )
    with pytest.raises(TimeoutError):
        listener.write_transcript(tmp_path / "transcript.jsonl", listening)
    assert not (tmp_path / "marker").exists()


def test_the_requested_language_reaches_the_recognizer(tmp_path, monkeypatch):
    transcribe = Mock(return_value="oi")
    monkeypatch.setattr(listener.transcriber, "transcribe", transcribe)
    assert listener.transcribe_when_ready(b"pcm", "pt") == "oi"
    transcribe.assert_called_once_with(b"pcm", "pt")


def test_settings_reach_the_listener_configuration(tmp_path, monkeypatch):
    monkeypatch.setattr(listen_cli, "systemctl", Mock())
    listen_cli.begin_listening(
        tmp_path, {"human": "AvatarRoomMicrophone"}, language="pt", barge_in=True
    )
    assert json.loads((tmp_path / "listener.json").read_text()) == {
        "sources": {"human": "AvatarRoomMicrophone"},
        "language": "pt",
        "barge_in": True,
    }


def test_silence_returns_nothing_and_keeps_the_place(tmp_path):
    assert utterances.next_utterance(tmp_path, 0, always_open) is None
    assert utterances.last_heard(tmp_path) == 0


def test_hearing_consumes_everything_said_since_the_last_turn(tmp_path, monkeypatch):
    monkeypatch.setattr(utterances, "SETTLE_SECONDS", 0)
    path = tmp_path / "transcript.jsonl"
    transcript_log.append(path, "human", "primeira parte")
    transcript_log.append(path, "human", "segunda parte")
    assert (
        utterances.next_utterance(tmp_path, 0, always_open)
        == "primeira parte segunda parte"
    )
    assert utterances.next_utterance(tmp_path, 0, always_open) is None


def test_hearing_waits_while_the_human_is_still_talking(tmp_path, monkeypatch):
    monkeypatch.setattr(utterances, "SETTLE_SECONDS", 0)
    monkeypatch.setattr(utterances, "POLL_SECONDS", 0.01)
    path = tmp_path / "transcript.jsonl"
    marker = tmp_path / listener.SPEECH_IN_PROGRESS_MARKER
    transcript_log.append(path, "human", "antes da pausa")
    marker.touch()

    def finish_speaking():
        transcript_log.append(path, "human", "depois da pausa")
        marker.unlink()

    threading.Timer(0.05, finish_speaking).start()
    assert (
        utterances.next_utterance(tmp_path, 0, always_open)
        == "antes da pausa depois da pausa"
    )


def test_a_closed_conversation_ends_the_wait_instead_of_hanging(tmp_path):
    with pytest.raises(utterances.ConversationClosed):
        utterances.next_utterance(tmp_path, 60, lambda: False)


def test_opening_again_keeps_the_conversation_and_what_was_not_heard(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(talk_cli, "conversation_open", lambda: True)
    bring_up = Mock()
    monkeypatch.setattr(start, "bring_up", bring_up)
    utterances.remember(tmp_path, 7)
    talk_cli.open_conversation(argparse.Namespace(language=None), tmp_path)
    bring_up.assert_not_called()
    assert json.loads(capsys.readouterr().out) == {"open": True, "last_heard": 7}


def test_opening_listens_only_to_the_cancelled_microphone(tmp_path, monkeypatch):
    monkeypatch.setattr(talk_cli, "conversation_open", lambda: False)
    monkeypatch.setattr(start, "bring_up", Mock())
    begin = Mock()
    monkeypatch.setattr(listen_cli, "begin_listening", begin)
    utterances.remember(tmp_path, 7)
    talk_cli.open_conversation(argparse.Namespace(language="pt"), tmp_path)
    begin.assert_called_once_with(
        tmp_path, {"human": "AvatarRoomMicrophone"}, language="pt", barge_in=True
    )
    assert utterances.last_heard(tmp_path) == 0


def test_a_failed_open_closes_what_it_started(tmp_path, monkeypatch):
    monkeypatch.setattr(talk_cli, "conversation_open", lambda: False)
    monkeypatch.setattr(start, "bring_up", Mock(side_effect=TimeoutError("late")))
    close = Mock()
    monkeypatch.setattr(talk_cli, "close_conversation", close)
    with pytest.raises(TimeoutError):
        talk_cli.open_conversation(argparse.Namespace(language=None), tmp_path)
    close.assert_called_once()


@pytest.mark.parametrize(
    ("meeting_running", "stops_everything"), [(False, True), (True, False)]
)
def test_closing_leaves_a_running_meeting_alone(
    tmp_path, monkeypatch, meeting_running, stops_everything
):
    runner = Mock()
    monkeypatch.setattr(talk_cli.subprocess, "run", runner)
    monkeypatch.setattr(talk_cli, "is_active", lambda unit: meeting_running)
    talk_cli.close_conversation(argparse.Namespace(), tmp_path)
    commands = [call.args[0] for call in runner.call_args_list]
    assert ["systemctl", "--user", "stop", "avatar-conversation.target"] in commands
    assert (["avatar-stop"] in commands) is stops_everything


def test_saying_plays_aloud_and_reports_the_speech_result(tmp_path, monkeypatch):
    runner = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(talk_cli.subprocess, "run", runner)
    with pytest.raises(SystemExit):
        talk_cli.say(
            argparse.Namespace(text="oi", emotion="happy", voice=None), tmp_path
        )
    runner.assert_called_once_with(
        ["avatar-command", "speak", "oi", "happy", "speakers"]
    )


def client(**fields):
    return {
        "class": desktop_window.WINDOW_CLASS,
        "title": "Avatar",
        "address": "0xa",
        "floating": False,
        "pinned": False,
        **fields,
    }


def fake_desktop(monkeypatch, clients):
    monitors = [
        {"focused": False},
        {
            "focused": True,
            "x": 1920,
            "y": 0,
            "width": 3840,
            "height": 2160,
            "scale": 2.0,
            "activeWorkspace": {"id": 4},
        },
    ]
    monkeypatch.setattr(
        desktop_window,
        "hyprctl_json",
        lambda kind: {"clients": clients, "monitors": monitors}[kind],
    )
    dispatch = Mock()
    monkeypatch.setattr(desktop_window, "dispatch", dispatch)
    return dispatch


def test_showing_floats_the_window_in_the_corner_of_the_focused_screen(monkeypatch):
    dispatch = fake_desktop(monkeypatch, [client()])
    desktop_window.show()
    assert [call.args for call in dispatch.call_args_list] == [
        ("movetoworkspacesilent", "4,address:0xa"),
        ("togglefloating", "address:0xa"),
        ("resizewindowpixel", "exact 640 360,address:0xa"),
        ("movewindowpixel", "exact 3176 696,address:0xa"),
        ("pin", "address:0xa"),
    ]


def test_showing_twice_does_not_toggle_floating_or_pinning_off(monkeypatch):
    dispatch = fake_desktop(monkeypatch, [client(floating=True, pinned=True)])
    desktop_window.show()
    assert "togglefloating" not in [call.args[0] for call in dispatch.call_args_list]
    assert "pin" not in [call.args[0] for call in dispatch.call_args_list]


def test_the_controls_window_is_never_taken_for_the_avatar(monkeypatch):
    fake_desktop(
        monkeypatch,
        [client(title=desktop_window.CONTROLS_TITLE, address="0xc"), client()],
    )
    assert desktop_window.avatar_window()["address"] == "0xa"


def test_hiding_unpins_before_returning_to_the_hidden_workspace(monkeypatch):
    dispatch = fake_desktop(monkeypatch, [client(pinned=True)])
    desktop_window.hide()
    assert [call.args for call in dispatch.call_args_list] == [
        ("pin", "address:0xa"),
        ("movetoworkspacesilent", "special:avatar,address:0xa"),
    ]


def test_hiding_a_window_that_is_already_gone_succeeds(monkeypatch):
    dispatch = fake_desktop(monkeypatch, [])
    desktop_window.hide()
    dispatch.assert_not_called()


def test_the_room_microphone_cancels_everything_the_desktop_plays():
    configuration = (
        Path(__file__).resolve().parents[2] / "room-microphone.conf"
    ).read_text()
    assert "monitor.mode = true" in configuration
    assert f'"{talk_cli.ROOM_MICROPHONE}"' in configuration
