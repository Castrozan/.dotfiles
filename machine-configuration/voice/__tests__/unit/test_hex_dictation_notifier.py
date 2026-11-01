import json
import subprocess
from pathlib import Path

import hex_dictation_notifier
from hex_dictation_notifier import (
    NOTIFICATION_REFRESH_SECONDS,
    DictationNotifier,
    follow_dictation_events,
    read_dictation_phase,
)


class RecordedCommands:
    def __init__(self, next_notification_id="41"):
        self.commands = []
        self.next_notification_id = next_notification_id

    def __call__(self, command):
        self.commands.append(command)
        return subprocess.CompletedProcess(command, 0, self.next_notification_id, "")


def dictation_event(phase, text=""):
    return json.dumps({"kind": "dictation", "phase": phase, "text": text})


def test_read_dictation_phase_ignores_everything_but_dictation_events():
    assert read_dictation_phase(dictation_event("started")) == "started"
    assert read_dictation_phase('{"kind":"state","state":"dictating"}') is None
    assert read_dictation_phase("not json") is None
    assert read_dictation_phase("[1]") is None


def test_started_raises_a_critical_recording_notification():
    commands = RecordedCommands()
    DictationNotifier(commands).handle_event(dictation_event("started"))
    assert commands.commands == [
        [
            "notify-send",
            "--app-name=Hex",
            "--urgency=critical",
            "--print-id",
            "--replace-id=0",
            "Hex recording",
            "Release the keys to transcribe",
        ]
    ]


def test_transcribing_replaces_the_recording_notification():
    commands = RecordedCommands()
    notifier = DictationNotifier(commands)
    notifier.handle_event(dictation_event("started"))
    notifier.handle_event(dictation_event("transcribing"))
    assert "--replace-id=41" in commands.commands[1]
    assert "Hex transcribing" in commands.commands[1]
    assert notifier.refresh_timeout_seconds is None


def test_every_ending_phase_closes_the_notification():
    for ending_phase in ("pasted", "printed", "discarded", "cancelled", "voice_action"):
        commands = RecordedCommands()
        notifier = DictationNotifier(commands)
        notifier.handle_event(dictation_event("started"))
        notifier.handle_event(dictation_event(ending_phase))
        assert commands.commands[1][-2:] == ["u", "41"]
        assert notifier.refresh_timeout_seconds is None


def test_ending_with_nothing_shown_runs_nothing():
    commands = RecordedCommands()
    DictationNotifier(commands).handle_event(dictation_event("repasted"))
    DictationNotifier(commands).handle_event(dictation_event("pasted"))
    assert commands.commands == []


def test_failure_shows_the_reason_and_never_the_transcript():
    commands = RecordedCommands()
    notifier = DictationNotifier(commands)
    notifier.handle_event(
        dictation_event({"failed": "paste refused"}, text="private words")
    )
    assert commands.commands[0][-2:] == ["Hex dictation failed", "paste refused"]
    assert "private words" not in str(commands.commands)


def test_transcript_text_never_reaches_a_notification():
    commands = RecordedCommands()
    notifier = DictationNotifier(commands)
    for phase in ("started", "transcribing", "pasted"):
        notifier.handle_event(dictation_event(phase, text="private words"))
    assert "private words" not in str(commands.commands)


def test_refresh_keeps_a_long_recording_on_screen():
    commands = RecordedCommands()
    notifier = DictationNotifier(commands)
    notifier.handle_event(dictation_event("started"))
    assert notifier.refresh_timeout_seconds == NOTIFICATION_REFRESH_SECONDS
    notifier.refresh()
    assert commands.commands[1] == [
        "notify-send",
        "--app-name=Hex",
        "--urgency=critical",
        "--print-id",
        "--replace-id=41",
        "Hex recording",
        "Release the keys to transcribe",
    ]


def test_unavailable_notification_daemon_keeps_the_notifier_alive():
    def refusing_daemon(command):
        return subprocess.CompletedProcess(command, 1, "", "no daemon")

    notifier = DictationNotifier(refusing_daemon)
    notifier.handle_event(dictation_event("started"))
    notifier.handle_event(dictation_event("pasted"))
    assert notifier.refresh_timeout_seconds is None


def test_follow_handles_lines_that_arrive_together_then_reports_the_tail_ending(
    tmp_path: Path,
):
    event_log = tmp_path / "live.ndjson"
    event_log.write_text(
        dictation_event("started") + "\n" + dictation_event("pasted") + "\n"
    )
    commands = RecordedCommands()

    exit_code = follow_dictation_events(
        ["cat", str(event_log)], DictationNotifier(commands)
    )

    assert exit_code == 1
    assert len(commands.commands) == 2
    assert commands.commands[0][0] == "notify-send"
    assert commands.commands[1][0] == "busctl"


def test_follow_refreshes_while_recording_without_a_new_event(monkeypatch):
    monkeypatch.setattr(hex_dictation_notifier, "NOTIFICATION_REFRESH_SECONDS", 0.01)
    commands = RecordedCommands()

    exit_code = follow_dictation_events(
        ["sh", "-c", f"echo '{dictation_event('started')}'; sleep 0.1"],
        DictationNotifier(commands),
    )

    assert exit_code == 1
    assert len(commands.commands) >= 3
