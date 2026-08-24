import os
import tempfile

import pytest
from audio_capture import AudioCapture
from process_execution import CommandResult
from signal_files import default_signal_file_paths
from speech_synthesizer import SpeechSynthesizer


@pytest.fixture
def temporary_home(monkeypatch, tmp_path):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(tempfile, "tempdir", None)
    return tmp_path


def test_the_signal_files_follow_tmpdir_and_carry_no_process_id(temporary_home):
    paths = default_signal_file_paths()

    assert paths.followup_flag == temporary_home / "hey-bot-followup"
    assert paths.wait_context == temporary_home / "hey-bot-wait-context"
    assert str(os.getpid()) not in str(paths.followup_flag)
    assert str(os.getpid()) not in str(paths.wait_context)


def test_the_keywords_disabled_flag_keeps_the_path_its_writers_agreed_on(
    temporary_home,
):
    assert str(default_signal_file_paths().keywords_disabled) == (
        "/tmp/hey-bot-keywords-disabled"
    )


def test_a_recorded_chunk_is_created_under_tmpdir(temporary_home):
    chunk_path = AudioCapture().create_chunk_file()

    assert chunk_path.parent == temporary_home
    assert chunk_path.name.startswith("hey-bot-")
    assert chunk_path.suffix == ".wav"


def test_rendered_speech_is_created_under_tmpdir_and_removed_afterwards(
    temporary_home,
):
    rendered_paths = []

    def run_process(arguments, merge_error_output=False):
        if arguments[0] == "edge-tts":
            rendered_paths.append(arguments[arguments.index("--write-media") + 1])
        return CommandResult(0, "")

    SpeechSynthesizer("en-US-JennyNeural", run_process=run_process).speak("hello")

    assert os.path.dirname(rendered_paths[0]) == str(temporary_home)
    assert os.path.basename(rendered_paths[0]).startswith("hey-bot-tts-")
    assert not os.path.exists(rendered_paths[0])
