import json

import media_speech_cli
import pytest
from media_speech.contract import SpeechError, SpeechRequest
from media_speech.discovery import VoiceQuery
from media_speech.kokoro_provider import KokoroSpeechProvider, KokoroVoiceCatalog
from media_speech_cli import main


def test_provider_discovery_needs_no_credentials_runtime_or_operation_state(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        media_speech_cli,
        "read_elevenlabs_api_key",
        lambda: pytest.fail("credential read"),
    )
    monkeypatch.delenv("MEDIA_KOKORO_MODEL", raising=False)
    state = tmp_path / "operations"
    assert main(["--state-directory", str(state), "providers"]) == 0
    output = capsys.readouterr()
    providers = json.loads(output.out)["providers"]
    assert [provider["provider"] for provider in providers] == ["kokoro", "elevenlabs"]
    local, cloud = providers
    assert local["alignment"] == "unavailable"
    assert local["requires_payment"] is False
    assert cloud["model"] == "eleven_multilingual_v2"
    assert cloud["language_enforcement"] is False
    assert cloud["alignment"] == "character"
    assert cloud["requires_credentials"] is True
    assert all(provider["maximum_text_characters"] == 4000 for provider in providers)
    assert not output.err
    assert not state.exists()


def test_local_voice_pages_cover_exactly_the_generation_contract(tmp_path):
    runtime = tmp_path / "runtime"
    runtime.write_bytes(b"fixture")
    provider = KokoroSpeechProvider(runtime, runtime, runtime, tmp_path)
    catalog = KokoroVoiceCatalog()
    voices = []
    token = None
    while True:
        page = catalog.list_voices(VoiceQuery(page_size=2, page_token=token))
        assert len(page.voices) == 2
        voices.extend(page.voices)
        token = page.next_page_token
        if token is None:
            break
    assert len({voice.voice_id for voice in voices}) == 6
    assert {voice.voice_id for voice in voices if voice.language == "pt-br"} == {
        "pf_dora",
        "pm_alex",
        "pm_santa",
    }
    for voice in voices:
        provider.preflight(SpeechRequest("Hello", voice.voice_id, voice.language))
        other_language = "pt-br" if voice.language == "en-us" else "en-us"
        request = SpeechRequest("Hello", voice.voice_id, other_language)
        with pytest.raises(SpeechError, match="unsupported_voice"):
            provider.preflight(request)


@pytest.mark.parametrize(
    "search,expected",
    [("DORA", ["pf_dora"]), ("pm_", ["pm_alex", "pm_santa"]), ("absent", [])],
)
def test_local_voice_search_is_read_only_without_model_files(
    tmp_path, monkeypatch, capsys, search, expected
):
    monkeypatch.delenv("MEDIA_KOKORO_MODEL", raising=False)
    state = tmp_path / "operations"
    assert (
        main(
            [
                "--state-directory",
                str(state),
                "voices",
                "--provider",
                "kokoro",
                "--search",
                search,
            ]
        )
        == 0
    )
    output = capsys.readouterr()
    page = json.loads(output.out)
    assert [voice["voice_id"] for voice in page["voices"]] == expected
    assert page["next_page_token"] is None
    assert not output.err
    assert not state.exists()


@pytest.mark.parametrize("token", ["-1", "not-a-token", "6", "1" * 4096])
def test_invalid_local_page_tokens_are_categorized(token):
    catalog = KokoroVoiceCatalog()
    query = VoiceQuery(page_token=token)
    with pytest.raises(SpeechError, match="invalid_page_token"):
        catalog.list_voices(query)


@pytest.mark.parametrize(
    "arguments,category",
    [
        ({"page_size": 0}, "invalid_page_size"),
        ({"page_size": 101}, "invalid_page_size"),
        ({"page_token": ""}, "invalid_page_token"),
        ({"page_token": "x" * 4097}, "invalid_page_token"),
        ({"search": " "}, "invalid_voice_search"),
        ({"search": "x" * 201}, "invalid_voice_search"),
    ],
)
def test_invalid_catalog_queries_fail_before_network(arguments, category):
    with pytest.raises(SpeechError, match=category):
        VoiceQuery(**arguments)


def test_cloud_discovery_without_credentials_writes_no_operation(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(media_speech_cli, "read_elevenlabs_api_key", lambda: None)
    state = tmp_path / "operations"
    assert (
        main(["--state-directory", str(state), "voices", "--provider", "elevenlabs"])
        == 1
    )
    output = capsys.readouterr()
    assert json.loads(output.err) == {"error": "missing_credentials"}
    assert not output.out
    assert not state.exists()


def test_generation_help_explains_voice_discovery_and_optional_uuid(capsys):
    with pytest.raises(SystemExit) as exit:
        main(["generate", "--help"])
    assert exit.value.code == 0
    help_text = " ".join(capsys.readouterr().out.split())
    assert "voice_id from 'media-speech voices --provider PROVIDER'" in help_text
    assert "Optional UUID; generated when omitted" in help_text
    assert "at most 4,000 characters" in help_text
