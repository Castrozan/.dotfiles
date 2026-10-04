import base64
import json

import httpx
import pytest
from elevenlabs.client import ElevenLabs
from media_speech.contract import SpeechError, SpeechRequest
from media_speech.elevenlabs_provider import ElevenLabsSpeechProvider


def test_sdk_serializes_the_contract_and_preserves_usage_and_alignment():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(
            200,
            headers={"request-id": "provider-receipt", "character-cost": "2"},
            json={
                "audio_base64": base64.b64encode(b"\x00\x01" * 24000).decode(),
                "alignment": {
                    "characters": ["H", "i"],
                    "character_start_times_seconds": [0, 0.2],
                    "character_end_times_seconds": [0.2, 0.5],
                },
                "normalized_alignment": None,
            },
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        client = ElevenLabs(api_key="test-only", httpx_client=transport)
        result = ElevenLabsSpeechProvider("test-only", client).synthesize(
            SpeechRequest("Hi", "voice", "en-us")
        )
    assert len(requests) == 1
    assert requests[0].url.path == "/v1/text-to-speech/voice/with-timestamps"
    assert requests[0].url.params["output_format"] == "pcm_24000"
    assert json.loads(requests[0].content)["model_id"] == "eleven_multilingual_v2"
    assert json.loads(requests[0].content)["language_code"] == "en"
    assert result.provider_request_id == "provider-receipt"
    assert result.billed_characters == 2
    assert result.alignment.characters == ("H", "i")
    result.alignment.validate(1)


@pytest.mark.parametrize(
    "status,category",
    [
        (401, "authentication_failed"),
        (402, "insufficient_balance"),
        (429, "rate_limited"),
        (500, "provider_failed"),
    ],
)
def test_paid_errors_never_retry_or_expose_provider_bodies(status, category):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(status, json={"detail": "secret provider body"})

    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        client = ElevenLabs(api_key="test-only", httpx_client=transport)
        with pytest.raises(SpeechError, match=category) as error:
            ElevenLabsSpeechProvider("test-only", client).synthesize(
                SpeechRequest("Hi", "voice", "en-us")
            )
    assert len(calls) == 1
    assert "secret" not in str(error.value)


def test_absent_alignment_and_usage_are_explicitly_absent():
    def respond(request):
        return httpx.Response(
            200,
            json={
                "audio_base64": "AAE=",
                "alignment": None,
                "normalized_alignment": None,
            },
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        client = ElevenLabs(api_key="test-only", httpx_client=transport)
        result = ElevenLabsSpeechProvider("test-only", client).synthesize(
            SpeechRequest("Hi", "voice", "en-us")
        )
    assert result.alignment is None
    assert result.billed_characters is None
