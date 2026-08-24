from pathlib import Path

import pytest
from audio_capture import CHUNK_DURATION_SECONDS, ENERGY_THRESHOLD, AudioCapture
from process_execution import CommandResult
from speech_transcriber import SpeechTranscriber

CHUNK_PATH = Path("/tmp/hey-bot-chunk.wav")


def amplitude_report(amplitude):
    return f"Samples read:     96000\nMaximum amplitude:     {amplitude}\n"


def capture_reading(amplitude):
    def run_process(_arguments, merge_error_output=False):
        return CommandResult(0, amplitude_report(amplitude))

    return AudioCapture(run_process=run_process)


@pytest.mark.parametrize(
    ("amplitude", "expected"),
    [
        ("0.500000", True),
        (f"{ENERGY_THRESHOLD:.6f}", True),
        ("0.010000", False),
    ],
)
def test_only_a_chunk_at_or_above_the_energy_threshold_carries_audio(
    amplitude, expected
):
    assert capture_reading(amplitude).chunk_has_audio(CHUNK_PATH) is expected


def test_a_chunk_without_an_amplitude_reading_carries_no_audio():
    capture = AudioCapture(
        run_process=lambda _arguments, merge_error_output=False: CommandResult(1, "")
    )

    assert capture.chunk_has_audio(CHUNK_PATH) is False


def test_the_recorder_captures_one_mono_chunk_at_the_carried_duration():
    started = []
    capture = AudioCapture(start_process=lambda arguments: started.append(arguments))

    capture.start_chunk_recording(CHUNK_PATH)

    assert started == [
        [
            "rec",
            "-q",
            str(CHUNK_PATH),
            "rate",
            "16k",
            "channels",
            "1",
            "trim",
            "0",
            str(CHUNK_DURATION_SECONDS),
        ]
    ]


def transcriber_answering(whisper_output, recorded_arguments):
    def run_process(arguments, merge_error_output=False):
        recorded_arguments.append(arguments)
        return CommandResult(0, whisper_output)

    return SpeechTranscriber("/models/ggml-base.bin", run_process=run_process)


def test_the_transcriber_asks_whisper_for_a_bare_auto_language_transcription():
    recorded_arguments = []

    transcriber_answering("hello there\n", recorded_arguments).transcribe(CHUNK_PATH)

    assert recorded_arguments == [
        [
            "whisper-cli",
            "-m",
            "/models/ggml-base.bin",
            "-f",
            str(CHUNK_PATH),
            "-nt",
            "-np",
            "-l",
            "auto",
            "--suppress-nst",
        ]
    ]


def test_a_hallucinated_transcription_is_discarded():
    transcriber = transcriber_answering("こんにちは 世界 元気ですか\n", [])

    assert transcriber.transcribe(CHUNK_PATH) == ""


def test_a_spoken_transcription_survives_cleaning():
    transcriber = transcriber_answering("  the coffee  machine\nis running \n", [])

    assert transcriber.transcribe(CHUNK_PATH) == "the coffee machine is running"
