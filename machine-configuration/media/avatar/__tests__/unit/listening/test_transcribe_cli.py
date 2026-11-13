import io
from unittest.mock import Mock

from transcription import transcriber


def test_the_transcript_of_the_pcm_on_stdin_is_printed(monkeypatch, capsys):
    transcribed = Mock(return_value="hey Voyager, check the build")
    monkeypatch.setattr(transcriber, "transcribe", transcribed)
    monkeypatch.setattr(
        transcriber.sys, "stdin", io.TextIOWrapper(io.BytesIO(b"\x01\x02" * 320))
    )
    transcriber.main()
    transcribed.assert_called_once_with(b"\x01\x02" * 320)
    assert capsys.readouterr().out == "hey Voyager, check the build\n"


def test_silence_prints_an_empty_line(monkeypatch, capsys):
    monkeypatch.setattr(transcriber, "transcribe", Mock(return_value=""))
    monkeypatch.setattr(transcriber.sys, "stdin", io.TextIOWrapper(io.BytesIO(b"")))
    transcriber.main()
    assert capsys.readouterr().out == "\n"
