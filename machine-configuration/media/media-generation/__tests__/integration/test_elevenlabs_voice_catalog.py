import json

import httpx
import media_speech_cli
import pytest
from elevenlabs.client import ElevenLabs
from media_speech.contract import SpeechError
from media_speech.discovery import VoiceQuery
from media_speech.elevenlabs_provider import ElevenLabsSpeechProvider


def test_voice_catalog_uses_sdk_pagination_and_returns_ids_without_operations(
    tmp_path, monkeypatch, capsys
):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "voices": [
                    {
                        "voice_id": "EXAVITQu4vr4xnSDxMaL",
                        "name": "Sarah",
                        "preview_url": "https://example.test/preview.mp3",
                    }
                ],
                "has_more": True,
                "next_page_token": "opaque-next",
                "total_count": 2,
            },
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        client = ElevenLabs(api_key="test-only", httpx_client=transport)
        monkeypatch.setattr(
            media_speech_cli, "read_elevenlabs_api_key", lambda: "test-only"
        )
        monkeypatch.setattr(
            media_speech_cli,
            "ElevenLabsSpeechProvider",
            lambda key: ElevenLabsSpeechProvider(key, client),
        )
        state = tmp_path / "operations"
        assert (
            media_speech_cli.main(
                [
                    "--state-directory",
                    str(state),
                    "voices",
                    "--provider",
                    "elevenlabs",
                    "--page-size",
                    "1",
                    "--page-token",
                    "opaque-previous",
                    "--search",
                    "Sarah",
                ]
            )
            == 0
        )
    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert requests[0].url.path == "/v2/voices"
    assert dict(requests[0].url.params) == {
        "page_size": "1",
        "next_page_token": "opaque-previous",
        "search": "Sarah",
    }
    output = capsys.readouterr()
    page = json.loads(output.out)
    assert page["voices"][0]["voice_id"] == "EXAVITQu4vr4xnSDxMaL"
    assert page["voices"][0]["language"] is None
    assert page["next_page_token"] == "opaque-next"
    assert "test-only" not in output.out + output.err
    assert not state.exists()


@pytest.mark.parametrize(
    "status,category",
    [
        (401, "authentication_failed"),
        (403, "permission_denied"),
        (429, "rate_limited"),
        (500, "provider_failed"),
    ],
)
def test_catalog_errors_never_retry_or_expose_provider_bodies(status, category):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(status, json={"detail": "secret provider body"})

    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        client = ElevenLabs(api_key="test-only", httpx_client=transport)
        catalog = ElevenLabsSpeechProvider("test-only", client)
        query = VoiceQuery()
        with pytest.raises(SpeechError, match=category) as error:
            catalog.list_voices(query)
    assert len(calls) == 1
    assert "secret" not in str(error.value)


def test_catalog_network_errors_are_categorized_without_request_details():
    calls = []

    def respond(request):
        calls.append(request)
        raise httpx.ReadTimeout("secret request details", request=request)

    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        client = ElevenLabs(api_key="test-only", httpx_client=transport)
        catalog = ElevenLabsSpeechProvider("test-only", client)
        query = VoiceQuery()
        with pytest.raises(SpeechError, match="provider_unavailable") as error:
            catalog.list_voices(query)
    assert len(calls) == 1
    assert "secret" not in str(error.value)


@pytest.mark.parametrize(
    "response",
    [
        {"voices": [], "has_more": True, "total_count": 1},
        {"has_more": False, "total_count": 0},
        {"voices": None, "has_more": False, "total_count": 0},
        {"voices": [{"voice_id": "../invalid"}], "has_more": False, "total_count": 1},
        {"voices": [{"voice_id": None}], "has_more": False, "total_count": 1},
        {"voices": [], "has_more": True, "next_page_token": 123, "total_count": 1},
    ],
)
def test_incomplete_catalog_responses_do_not_claim_a_complete_page(response):
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=response)
        )
    ) as transport:
        client = ElevenLabs(api_key="test-only", httpx_client=transport)
        catalog = ElevenLabsSpeechProvider("test-only", client)
        query = VoiceQuery()
        with pytest.raises(SpeechError, match="invalid_provider_response"):
            catalog.list_voices(query)


def test_empty_final_catalog_page_is_valid():
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, json={"voices": [], "has_more": False, "total_count": 0}
            )
        )
    ) as transport:
        client = ElevenLabs(api_key="test-only", httpx_client=transport)
        page = ElevenLabsSpeechProvider("test-only", client).list_voices(VoiceQuery())
    assert page.voices == ()
    assert page.next_page_token is None
