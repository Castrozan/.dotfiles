import json
import stat
import struct

import pytest

import listen_cli
import listener
import speech_segmenter
import transcriber
import transcript_log

FRAME_SAMPLES = 480


def frame(amplitude):
    return struct.pack(f"<{FRAME_SAMPLES}h", *([amplitude] * FRAME_SAMPLES))


def feed(segmenter, frames):
    return [segment for item in frames if (segment := segmenter.feed(item))]


def test_silence_never_produces_a_segment():
    assert feed(speech_segmenter.SpeechSegmenter(), [frame(0)] * 200) == []


def test_speech_ending_in_silence_produces_one_segment_with_lead_in():
    frames = [frame(0)] * 20 + [frame(3000)] * 40 + [frame(0)] * 40
    segments = feed(speech_segmenter.SpeechSegmenter(), frames)
    assert len(segments) == 1
    assert len(segments[0]) > 40 * len(frame(0))


def test_a_click_too_short_to_be_speech_is_dropped():
    frames = [frame(3000)] * 3 + [frame(0)] * 40
    assert feed(speech_segmenter.SpeechSegmenter(), frames) == []


def test_unbroken_speech_is_cut_so_agents_hear_long_monologues_promptly():
    segments = feed(speech_segmenter.SpeechSegmenter(), [frame(3000)] * 900)
    assert len(segments) >= 2


def test_transcript_entries_are_sequenced_and_private(tmp_path):
    path = tmp_path / "transcript.jsonl"
    transcript_log.append(path, "meeting", "first")
    transcript_log.append(path, "human", "second")
    entries = transcript_log.read_since(path, 0)
    assert [(item["sequence"], item["source"], item["text"]) for item in entries] == [
        (1, "meeting", "first"),
        (2, "human", "second"),
    ]
    assert [item["text"] for item in transcript_log.read_since(path, 1)] == ["second"]
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_a_partially_written_line_is_not_read(tmp_path):
    path = tmp_path / "transcript.jsonl"
    transcript_log.append(path, "meeting", "complete")
    with path.open("a") as output:
        output.write('{"sequence": 2, "te')
    assert len(transcript_log.read_since(path, 0)) == 1


def test_waiting_returns_empty_when_nothing_was_said(tmp_path):
    path = tmp_path / "transcript.jsonl"
    assert transcript_log.wait_since(path, 0, 0.05) == []


@pytest.mark.parametrize(
    "text", ["[BLANK_AUDIO]", " (music) ", "[ Silence ]", "", "*applause*"]
)
def test_non_speech_markers_are_not_transcript(text):
    assert transcriber.clean_transcript(text) == ""


def test_real_words_survive_with_trimmed_whitespace():
    assert transcriber.clean_transcript("  bom dia [risos] pessoal ") == (
        "bom dia [risos] pessoal"
    )


def test_wrapped_recognizer_lines_become_one_sentence():
    assert transcriber.clean_transcript("Bom dia,\n pessoal.") == "Bom dia, pessoal."


def test_segments_are_posted_as_wav():
    wav = transcriber.wav_bytes(frame(1000))
    assert wav[:4] == b"RIFF"
    assert wav[8:12] == b"WAVE"


def test_capture_never_falls_back_to_another_device():
    command = listener.capture_command("@DEFAULT_MONITOR@")
    assert "--device=@DEFAULT_MONITOR@" in command
    assert "--property=node.dont-reconnect=true" in command
    assert "--property=node.dont-fallback=true" in command


def test_listening_starts_with_no_physical_microphone():
    assert listen_cli.selected_sources(None) == {"meeting": "@DEFAULT_MONITOR@"}


def test_a_named_microphone_is_a_separate_human_source(monkeypatch):
    monkeypatch.setattr(
        listen_cli, "existing_sources", lambda: {"alsa_input.usb.mono-fallback"}
    )
    sources = listen_cli.selected_sources("alsa_input.usb.mono-fallback")
    assert sources["human"] == "alsa_input.usb.mono-fallback"


@pytest.mark.parametrize(
    "source",
    ["AvatarMicrophone", "AvatarMic.monitor", "AvatarMix.monitor", "missing.source"],
)
def test_avatar_outputs_and_unknown_sources_cannot_be_the_microphone(
    source, monkeypatch
):
    monkeypatch.setattr(
        listen_cli,
        "existing_sources",
        lambda: {"AvatarMicrophone", "AvatarMic.monitor", "AvatarMix.monitor"},
    )
    with pytest.raises(ValueError):
        listen_cli.selected_sources(source)


def test_reading_prints_entries_after_the_sequence(tmp_path, capsys):
    path = tmp_path / "transcript.jsonl"
    transcript_log.append(path, "meeting", "one")
    transcript_log.append(path, "meeting", "two")
    listen_cli.print_entries(transcript_log.read_since(path, 1))
    printed = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [item["text"] for item in printed] == ["two"]
