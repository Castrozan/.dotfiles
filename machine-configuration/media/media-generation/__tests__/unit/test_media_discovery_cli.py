import json

import jsonschema
import pytest

import media_image_cli
import media_movie_cli
import media_speech_cli
from media_movie.request_reader import read_movie_request
from media_speech.contract import SpeechError
from media_speech.delivery import direct_speech_text


@pytest.mark.parametrize(
    "main,command",
    [
        (media_image_cli.main, "providers"),
        (media_movie_cli.main, "providers"),
        (media_movie_cli.main, "example"),
        (media_movie_cli.main, "schema"),
        (media_speech_cli.main, "providers"),
    ],
)
def test_discovery_is_machine_readable_without_state_or_credentials(
    tmp_path, capsys, main, command
):
    state = tmp_path / "state"
    assert main(["--state-directory", str(state), command]) == 0
    assert isinstance(json.loads(capsys.readouterr().out), dict)
    assert not state.exists()


def test_movie_example_matches_published_schema_and_runtime_reader(capsys):
    assert media_movie_cli.main(["example"]) == 0
    document = json.loads(capsys.readouterr().out)
    assert media_movie_cli.main(["schema"]) == 0
    schema = json.loads(capsys.readouterr().out)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(document, schema)
    assert read_movie_request(document).width == 1080
    document["scenes"][0]["motion"] = "invented_camera"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(document, schema)


def test_validate_checks_credentials_without_job_state(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-only")
    state = tmp_path / "state"
    assert (
        media_image_cli.main(
            [
                "--state-directory",
                str(state),
                "validate",
                "--provider",
                "openai",
                "--model",
                "gpt-image-2.5-flare",
                "--aspect-ratio",
                "1:1",
                "--quality",
                "low",
                "--prompt",
                "Mountain",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["status"] == "valid"
    monkeypatch.setenv("ELEVENLABS_API_KEY", "fixture-only")
    assert (
        media_speech_cli.main(
            [
                "--state-directory",
                str(state),
                "validate",
                "--provider",
                "elevenlabs",
                "--model",
                "eleven_v4",
                "--directions",
                "curious",
                "--voice",
                "voice",
                "--language",
                "en-us",
                "--text",
                "Hello.",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["model"] == "eleven_v4"
    assert not state.exists()


@pytest.mark.parametrize(
    "provider,model",
    [
        ("kokoro", "kokoro-v1.0-int8-model-files-v1.0"),
        ("elevenlabs", None),
        ("elevenlabs", "eleven_multilingual_v2"),
    ],
)
def test_unsupported_direction_control_is_rejected(provider, model):
    with pytest.raises(SpeechError, match="unsupported_delivery_instructions"):
        direct_speech_text("Hello", provider, model, "whispers")


def test_movie_inspection_needs_no_provider_runtime(
    tmp_path, monkeypatch, capsys, operation_id
):
    for variable in (
        "MEDIA_MOVIE_FFMPEG",
        "MEDIA_MOVIE_FFPROBE",
        "MEDIA_IMAGE_COMMAND",
        "MEDIA_SPEECH_COMMAND",
    ):
        monkeypatch.delenv(variable, raising=False)
    assert (
        media_movie_cli.main(
            ["--state-directory", str(tmp_path), "inspect", operation_id]
        )
        == 1
    )
    assert json.loads(capsys.readouterr().err)["error"] == "operation_unavailable"
