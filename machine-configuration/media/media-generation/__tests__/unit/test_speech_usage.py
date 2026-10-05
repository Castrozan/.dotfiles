import json
from dataclasses import asdict

import media_speech_cli
import pytest
from media_speech.contract import SpeechError
from media_speech.usage import (
    ProviderUsage,
    ProviderUsageService,
    UsageCapabilities,
    UsageQuota,
)


class TokenUsageReader:
    name = "another-provider"
    capabilities = UsageCapabilities("available", "account", ("tokens",))

    def __init__(self):
        self.calls = 0

    def read_usage(self):
        self.calls += 1
        return ProviderUsage(
            self.name,
            "available",
            "account",
            1000,
            (UsageQuota("tokens", "tokens", 25, 100, 2000),),
        )


def test_public_usage_service_consumes_a_provider_neutral_port():
    reader = TokenUsageReader()
    api = ProviderUsageService(reader)
    assert api.capabilities() == reader.capabilities
    snapshot = asdict(api.read_usage())
    assert snapshot["provider"] == "another-provider"
    assert snapshot["quotas"][0]["remaining"] == 75
    assert snapshot["quotas"][0]["unit"] == "tokens"
    assert reader.calls == 1


def test_usage_service_rejects_identity_or_capability_mismatch():
    reader = TokenUsageReader()
    snapshot = reader.read_usage()
    reader.name = "different-provider"
    reader.read_usage = lambda: snapshot
    with pytest.raises(SpeechError, match="invalid_provider_response"):
        ProviderUsageService(reader).read_usage()


def test_unknown_and_exhausted_quota_are_distinct():
    assert UsageQuota("tokens", "tokens", 5, None).remaining is None
    assert UsageQuota("tokens", "tokens", None, 100).remaining is None
    assert UsageQuota("tokens", "tokens", 110, 100).remaining == 0


@pytest.mark.parametrize(
    "capabilities",
    [
        UsageCapabilities("available", "project", ("tokens",)),
        UsageCapabilities("available", "account", ("requests",)),
        UsageCapabilities("unavailable", "account", ()),
    ],
)
def test_snapshot_must_match_discovered_usage_capabilities(capabilities):
    reader = TokenUsageReader()
    reader.capabilities = capabilities
    with pytest.raises(SpeechError, match="invalid_provider_response"):
        ProviderUsageService(reader).read_usage()


@pytest.mark.parametrize("used", [-1, True, float("inf"), float("nan"), "25"])
def test_invalid_quota_measurements_are_refused(used):
    with pytest.raises(SpeechError, match="invalid_usage"):
        UsageQuota("tokens", "tokens", used, 100)


def test_local_usage_needs_no_credentials_runtime_or_operation_state(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        media_speech_cli,
        "read_elevenlabs_api_key",
        lambda: pytest.fail("credential read"),
    )
    monkeypatch.setattr(
        media_speech_cli,
        "SpeechService",
        lambda *args: pytest.fail("operation service"),
    )
    monkeypatch.delenv("MEDIA_KOKORO_MODEL", raising=False)
    state = tmp_path / "operations"
    assert (
        media_speech_cli.main(
            ["--state-directory", str(state), "usage", "--provider", "kokoro"]
        )
        == 0
    )
    output = capsys.readouterr()
    usage = json.loads(output.out)
    assert usage["provider"] == "kokoro"
    assert usage["status"] == "not_applicable"
    assert usage["scope"] == "local"
    assert usage["quotas"] == []
    assert usage["overage_charge"] is None
    assert usage["overage_enabled"] is None
    assert isinstance(usage["observed_at_unix"], int)
    assert not output.err
    assert not state.exists()


def test_provider_capabilities_include_usage_without_account_access(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(
        media_speech_cli,
        "read_elevenlabs_api_key",
        lambda: pytest.fail("credential read"),
    )
    monkeypatch.setattr(
        media_speech_cli,
        "SpeechService",
        lambda *args: pytest.fail("operation service"),
    )
    state = tmp_path / "operations"
    assert media_speech_cli.main(["--state-directory", str(state), "providers"]) == 0
    providers = json.loads(capsys.readouterr().out)["providers"]
    assert providers[0]["usage"] == {
        "status": "not_applicable",
        "scope": "local",
        "metrics": [],
    }
    assert providers[1]["usage"] == {
        "status": "available",
        "scope": "account",
        "metrics": ["credits", "voice_slots"],
    }
    assert not state.exists()


def test_cloud_usage_missing_credentials_is_categorized_without_state(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(media_speech_cli, "read_elevenlabs_api_key", lambda: None)
    state = tmp_path / "operations"
    assert (
        media_speech_cli.main(
            ["--state-directory", str(state), "usage", "--provider", "elevenlabs"]
        )
        == 1
    )
    output = capsys.readouterr()
    assert json.loads(output.err) == {"error": "missing_credentials"}
    assert not output.out
    assert not state.exists()


def test_unavailable_provider_usage_does_not_claim_an_unlimited_quota():
    capabilities = UsageCapabilities("unavailable", "account", ())
    snapshot = ProviderUsage("unsupported-meter", "unavailable", "account", 1000)
    assert capabilities.metrics == ()
    assert snapshot.quotas == ()
    with pytest.raises(SpeechError, match="invalid_usage"):
        ProviderUsage(
            "unsupported-meter",
            "unavailable",
            "account",
            1000,
            (UsageQuota("credits", "credits", 0, None),),
        )
