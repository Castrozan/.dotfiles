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
