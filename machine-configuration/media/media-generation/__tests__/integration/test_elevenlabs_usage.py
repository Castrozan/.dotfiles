import json

import httpx
import media_speech_cli
import pytest
from elevenlabs.client import ElevenLabs
from media_speech.contract import SpeechError
from media_speech.elevenlabs_usage import ElevenLabsUsageReader
from media_speech.usage import ProviderUsageService


def subscription_document():
    return {
        "tier": "creator",
        "status": "active",
        "character_count": 884,
        "character_limit": 131000,
        "next_character_count_reset_unix": 1793818887,
        "max_credit_limit_extension": 0,
        "current_overage": {"amount": "0", "currency": "usd"},
        "can_extend_character_limit": True,
        "allowed_to_extend_character_limit": False,
        "voice_slots_used": 2,
        "professional_voice_slots_used": 0,
        "voice_limit": 30,
        "voice_add_edit_counter": 0,
        "can_extend_voice_limit": False,
        "can_use_instant_voice_cloning": True,
        "can_use_professional_voice_cloning": True,
        "open_invoices": [],
        "has_open_invoices": False,
    }


def test_public_api_usage_calls_one_sdk_get_without_generation_or_state(
    tmp_path, monkeypatch, capsys
):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=subscription_document())

    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        client = ElevenLabs(api_key="test-only", httpx_client=transport)
        monkeypatch.setattr(
            media_speech_cli, "read_elevenlabs_api_key", lambda: "test-only"
        )
        monkeypatch.setattr(
            media_speech_cli,
            "ElevenLabsUsageReader",
            lambda key: ElevenLabsUsageReader(key, client),
        )
        state = tmp_path / "operations"
        assert (
            media_speech_cli.main(
                ["--state-directory", str(state), "usage", "--provider", "elevenlabs"]
            )
            == 0
        )
    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert requests[0].url.path == "/v1/user/subscription"
    output = capsys.readouterr()
    usage = json.loads(output.out)
    assert usage["provider"] == "elevenlabs"
    assert usage["status"] == "available"
    assert usage["scope"] == "account"
    assert usage["plan"] == "creator"
    assert usage["account_status"] == "active"
    assert usage["quotas"][0] == {
        "name": "credits",
        "unit": "credits",
        "used": 884,
        "limit": 131000,
        "remaining": 130116,
        "resets_at_unix": 1793818887,
    }
    assert usage["quotas"][1]["name"] == "voice_slots"
    assert usage["quotas"][1]["remaining"] == 28
    assert usage["overage_charge"] == {"amount": "0", "currency": "USD"}
    assert usage["overage_enabled"] is False
    assert "test-only" not in output.out + output.err
    assert not output.err
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
def test_usage_errors_never_retry_or_expose_provider_details(status, category):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(status, json={"detail": "private provider body"})

    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        client = ElevenLabs(api_key="test-only", httpx_client=transport)
        with pytest.raises(SpeechError, match=category) as error:
            ProviderUsageService(
                ElevenLabsUsageReader("test-only", client)
            ).read_usage()
    assert len(requests) == 1
    assert "private" not in str(error.value)


def test_usage_network_failure_is_categorized_without_details():
    def respond(request):
        raise httpx.ReadTimeout("private request details", request=request)

    with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
        client = ElevenLabs(api_key="test-only", httpx_client=transport)
        with pytest.raises(SpeechError, match="provider_unavailable"):
            ProviderUsageService(
                ElevenLabsUsageReader("test-only", client)
            ).read_usage()


@pytest.mark.parametrize(
    "changes",
    [
        {"character_count": -1},
        {"character_limit": -1},
        {"character_count": "invalid"},
        {"current_overage": {"amount": "NaN", "currency": "usd"}},
        {"max_credit_limit_extension": "bad"},
    ],
)
def test_invalid_account_usage_never_becomes_a_snapshot(changes):
    document = {**subscription_document(), **changes}
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=document)
        )
    ) as transport:
        client = ElevenLabs(api_key="test-only", httpx_client=transport)
        with pytest.raises(SpeechError, match="invalid_provider_response"):
            ProviderUsageService(
                ElevenLabsUsageReader("test-only", client)
            ).read_usage()


def test_absent_overage_evidence_remains_unknown():
    document = subscription_document()
    del document["current_overage"]
    del document["max_credit_limit_extension"]
    document["next_character_count_reset_unix"] = None
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=document)
        )
    ) as transport:
        client = ElevenLabs(api_key="test-only", httpx_client=transport)
        snapshot = ProviderUsageService(
            ElevenLabsUsageReader("test-only", client)
        ).read_usage()
    assert snapshot.overage_charge is None
    assert snapshot.overage_enabled is None
    assert snapshot.quotas[0].resets_at_unix is None


@pytest.mark.parametrize("status", [200, 500])
def test_api_closes_its_owned_transport_on_success_and_failure(monkeypatch, status):
    transport = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(status, json=subscription_document())
        )
    )
    monkeypatch.setattr(httpx, "Client", lambda **arguments: transport)
    api = ProviderUsageService(ElevenLabsUsageReader("test-only"))
    if status == 200:
        assert api.read_usage().quotas[0].used == 884
    else:
        with pytest.raises(SpeechError, match="provider_failed"):
            api.read_usage()
    assert transport.is_closed
