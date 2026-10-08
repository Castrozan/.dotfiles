import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


SCRIPT = Path(
    os.environ.get(
        "NOTIFY_SCRIPT_UNDER_TEST",
        str(Path(__file__).resolve().parents[2] / "scripts/notify.sh"),
    )
)
AUDIO_COMMANDS = {
    "edge-tts",
    "mpv",
    "wpctl",
    "paplay",
    "aplay",
    "pw-play",
    "ffplay",
    "say",
    "espeak",
    "spd-say",
}


@pytest.fixture
def notification_commands(tmp_path):
    executable_directory = tmp_path / "bin"
    executable_directory.mkdir()
    (executable_directory / "bash").symlink_to(shutil.which("bash"))
    command_log = tmp_path / "commands.jsonl"
    mock = executable_directory / "mock"
    mock.write_text(
        f"#!{sys.executable}\n"
        "import json, os, pathlib, sys\n"
        "command = pathlib.Path(sys.argv[0]).name\n"
        "with open(os.environ['NOTIFY_TEST_COMMAND_LOG'], 'a') as output:\n"
        "    output.write(json.dumps([command, *sys.argv[1:]]) + '\\n')\n"
        "if command == 'id': print('1000')\n"
        "if command == 'git': print('/nonexistent-notify-test-workspace')\n"
        "if command == 'jq': print('en-US-GuyNeural')\n"
        "if command == 'mktemp': print('/nonexistent-notify-test-audio.mp3')\n"
        "if command == 'notify-send': sys.exit(int(os.environ.get('NOTIFY_TEST_DESKTOP_EXIT', '0')))\n"
    )
    mock.chmod(0o755)
    for command in AUDIO_COMMANDS | {
        "notify-send",
        "curl",
        "id",
        "git",
        "jq",
        "mktemp",
        "rm",
    }:
        (executable_directory / command).symlink_to(mock)
    environment = {
        "PATH": str(executable_directory),
        "NOTIFY_TEST_COMMAND_LOG": str(command_log),
        "NTFY_TOPIC": "notification-test-topic",
    }

    def run(*arguments, desktop_exit=0):
        environment["NOTIFY_TEST_DESKTOP_EXIT"] = str(desktop_exit)
        result = subprocess.run(
            [str(executable_directory / "bash"), str(SCRIPT), *arguments],
            env=environment,
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        calls = [json.loads(line) for line in command_log.read_text().splitlines()]
        command_log.unlink()
        assert result.returncode == 0, result.stderr
        return calls

    return run


@pytest.mark.parametrize(
    "message",
    [
        "Work finished",
        "Critical issue: a solution is available",
        "Critical issue: another steward can fix it",
        "Critical issue: investigation is in progress",
        "Critical issue: repair is already claimed",
        "Critical issue: duplicate of the active incident",
        "Critical issue: peer ability is unknown",
        "Critical issue: active work is unknown",
        "Critical issue: no solution and nobody working on it",
        '{"severity":"critical","all_stewards_unable":true,"active_work":false}',
        "**Nightly_failed**: `no_comments_in_code` 34/35, <500ms",
        "API_KEY=synthetic-test-value and Bearer synthetic-test-value",
        "$(touch should-never-exist) `echo code`",
    ],
)
def test_missing_authoritative_escalation_evidence_always_keeps_text_only(
    notification_commands, message
):
    calls = notification_commands(message)
    assert not any(command[0] in AUDIO_COMMANDS for command in calls)
    desktop = [command for command in calls if command[0] == "notify-send"]
    assert len(desktop) == 1
    assert desktop[0][-1] == message
    assert "int:suppress-sound:1" in desktop[0]
    assert not any(command[0] == "curl" for command in calls)


def test_legacy_voice_argument_cannot_enable_speech(notification_commands):
    calls = notification_commands("Attention needed", "--voice", "en-US-GuyNeural")
    assert not any(command[0] in AUDIO_COMMANDS for command in calls)
    assert [command[-1] for command in calls if command[0] == "notify-send"] == [
        "Attention needed"
    ]


def test_repeated_notifications_remain_text_only(notification_commands):
    for _ in range(2):
        calls = notification_commands("Critical issue already under investigation")
        assert not any(command[0] in AUDIO_COMMANDS for command in calls)
        assert len([command for command in calls if command[0] == "notify-send"]) == 1


def test_mobile_text_delivery_survives_desktop_failure(notification_commands):
    calls = notification_commands("Alert 42", "--mobile", desktop_exit=1)
    assert not any(command[0] in AUDIO_COMMANDS for command in calls)
    assert len([command for command in calls if command[0] == "notify-send"]) == 1
    mobile = [command for command in calls if command[0] == "curl"]
    assert len(mobile) == 1
    assert mobile[0][-1] == "ntfy.sh/notification-test-topic"
    assert mobile[0][mobile[0].index("-d") + 1] == "Alert 42"


def test_default_message_is_preserved(notification_commands):
    calls = notification_commands()
    assert not any(command[0] in AUDIO_COMMANDS for command in calls)
    assert [command[-1] for command in calls if command[0] == "notify-send"] == ["Done"]
