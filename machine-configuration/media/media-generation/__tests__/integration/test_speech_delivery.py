import base64
import json

import httpx
import pytest
from elevenlabs.client import ElevenLabs

from media_speech.contract import SpeechRequest
from media_speech.delivery import direct_speech_text
from media_speech.elevenlabs_provider import ElevenLabsSpeechProvider


@pytest.mark.parametrize(
    "model",
    ["eleven_v4", "eleven_turbo_v2_5", "eleven_flash_v2_5", "eleven_multilingual_v2"],
)
def test_selected_model_and_supported_audio_tags_reach_official_sdk(model):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(
            200,
            headers={"request-id": "v4-job"},
            json={
                "audio_base64": base64.b64encode(b"\x00\x01" * 24000).decode(),
                "alignment": None,
                "normalized_alignment": None,
            },
        )

    text = direct_speech_text(
        "Hello. [whispers] The climb begins."
        if model == "eleven_v4"
        else "Hello. The climb begins.",
        "elevenlabs",
        model,
        "curious" if model == "eleven_v4" else None,
        "en-us",
    )
    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        client = ElevenLabs(api_key="fixture-only", httpx_client=transport)
        provider = ElevenLabsSpeechProvider("fixture-only", client, model=model)
        provider.preflight(SpeechRequest(text, "voice", "en-us"))
        result = provider.synthesize(SpeechRequest(text, "voice", "en-us"))
    assert len(calls) == 1
    assert calls[0].url.path.endswith("/with-timestamps")
    assert json.loads(calls[0].content)["model_id"] == model
    assert json.loads(calls[0].content)["text"] == (
        "[curious] Hello. [whispers] The climb begins."
        if model == "eleven_v4"
        else "Hello. The climb begins."
    )
    assert result.provider_request_id == "v4-job"
    assert result.alignment is None


def synthesized_request_body(text, model, language):
    calls = []

    def respond(request):
        calls.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "audio_base64": base64.b64encode(b"\x00\x01" * 24000).decode(),
                "alignment": None,
                "normalized_alignment": None,
            },
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        client = ElevenLabs(api_key="fixture-only", httpx_client=transport)
        ElevenLabsSpeechProvider("fixture-only", client, model=model).synthesize(
            SpeechRequest(text, "voice", language)
        )
    return calls[0]


@pytest.mark.parametrize(
    "directions,spoken_prefix",
    [
        (None, "[strong Brazilian Portuguese accent] "),
        (
            "warm and cheerful, smiling",
            "[warm and cheerful, smiling, strong Brazilian Portuguese accent] ",
        ),
    ],
)
def test_brazilian_portuguese_reaches_elevenlabs_as_the_primary_code_and_an_accent_cue(
    directions, spoken_prefix
):
    narration = "Eu gosto de dançar no domingo à tarde."
    body = synthesized_request_body(
        direct_speech_text(narration, "elevenlabs", "eleven_v4", directions, "pt-br"),
        "eleven_v4",
        "pt-br",
    )
    assert body["language_code"] == "pt"
    assert body["text"] == spoken_prefix + narration


@pytest.mark.parametrize(
    "provider,model",
    [
        ("kokoro", "kokoro-v1.0-int8-model-files-v1.0"),
        ("elevenlabs", "eleven_multilingual_v2"),
        ("elevenlabs", "eleven_flash_v2_5"),
    ],
)
def test_models_without_audio_tags_receive_the_portuguese_text_untouched(
    provider, model
):
    assert (
        direct_speech_text("Olá, Lucas.", provider, model, None, "pt-br")
        == "Olá, Lucas."
    )


def test_american_english_carries_no_accent_cue():
    assert (
        direct_speech_text("Hello.", "elevenlabs", "eleven_v4", None, "en-us")
        == "Hello."
    )
