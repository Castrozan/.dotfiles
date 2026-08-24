import tempfile

import pytest
from hey_bot import daemon_main
from hey_bot.daemon_main import build_daemon
from hey_bot.daemon_runtime import HeyBotDaemon
from hey_bot_boundary_fakes import (
    FakeGateway,
    RecordingNotifier,
    RecordingSynthesizer,
    content_reply,
)
from hey_bot_daemon_fakes import FakeCapture, ScriptedTranscriber
from hey_bot.push_to_talk_main import build_session
from hey_bot.push_to_talk_session import PushToTalkSession
from hey_bot.transcription_log_main import main as read_transcription_log

ENVIRONMENT = {
    "HEY_BOT_WHISPER_MODEL": "/models/ggml-base.bin",
    "HEY_BOT_KEYWORDS_PATTERN": "clever|jarvis",
    "HEY_BOT_GATEWAY_URL": "http://gateway.invalid",
    "HEY_BOT_AGENT_ID": "main",
    "HEY_BOT_TTS_VOICE": "en-US-JennyNeural",
    "HEY_BOT_MODEL": "test-model",
    "HEY_BOT_MAX_LOG_SIZE": "1048576",
}


@pytest.fixture
def deployed_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(tempfile, "tempdir", None)
    for name, value in ENVIRONMENT.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("HEY_BOT_GATEWAY_TOKEN_FILE", str(tmp_path / "gateway-token"))
    monkeypatch.setenv("HEY_BOT_TRANSCRIPTION_DIR", str(tmp_path / "transcriptions"))
    return tmp_path


def test_the_daemon_program_wires_itself_from_its_environment(deployed_environment):
    daemon = build_daemon()

    assert isinstance(daemon, HeyBotDaemon)
    assert (deployed_environment / "transcriptions").is_dir()


def test_the_push_to_talk_program_wires_itself_from_its_environment(
    deployed_environment,
):
    assert isinstance(build_session(), PushToTalkSession)


def test_a_dispatched_command_travels_from_the_wired_daemon_to_the_speech(
    deployed_environment, monkeypatch
):
    chunk_directory = deployed_environment / "chunks"
    chunk_directory.mkdir()
    spoken_replies = RecordingSynthesizer()
    monkeypatch.setattr(
        daemon_main, "AudioCapture", lambda: FakeCapture(chunk_directory)
    )
    monkeypatch.setattr(
        daemon_main,
        "SpeechTranscriber",
        lambda _model: ScriptedTranscriber(
            ["hey clever what is the weather", "in florianopolis today"]
        ),
    )
    monkeypatch.setattr(daemon_main, "DesktopNotifier", RecordingNotifier)
    monkeypatch.setattr(daemon_main, "SpeechSynthesizer", lambda _voice: spoken_replies)
    monkeypatch.setattr(
        daemon_main,
        "AssistantGateway",
        lambda _settings: FakeGateway(content_reply("The weather is fine.")),
    )
    daemon = build_daemon()

    for _chunk in range(5):
        daemon.process_chunk(chunk_directory / "chunk.wav")
    daemon.shut_down()

    assert spoken_replies.spoken == ["The weather is fine."]


def test_the_log_program_reports_a_transcription_directory_with_no_logs(
    deployed_environment, capsys
):
    (deployed_environment / "transcriptions").mkdir()

    exit_code = read_transcription_log([])

    assert exit_code == 1
    assert capsys.readouterr().out == (
        f"No transcription logs found in {deployed_environment / 'transcriptions'}\n"
    )
