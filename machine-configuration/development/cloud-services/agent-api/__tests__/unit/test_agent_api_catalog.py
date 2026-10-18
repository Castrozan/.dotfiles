import pytest
from jsonschema import Draft202012Validator

from agent_api.catalog import (
    capabilities,
    describe,
    discover,
    providers,
    validate_request,
)
from agent_api.contract import CapabilityError, OperationRequest, validate_url


def test_every_capability_has_a_valid_strict_input_schema_and_unique_id():
    entries = capabilities()
    assert len({entry["id"] for entry in entries}) == len(entries)
    for entry in entries:
        Draft202012Validator.check_schema(entry["input_schema"])
        assert entry["input_schema"]["additionalProperties"] is False
        assert entry["description"]
    assert all("input_schema" not in entry for entry in discover())
    assert {"fal", "monid"}.isdisjoint(entry["id"] for entry in providers())
    assert describe("web.search")["payment"] == "none"
    assert describe("web.scrape")["payment"] == "none"


@pytest.mark.parametrize("value", [0, 601, True, float("nan")])
def test_deadlines_are_finite_strict_and_bounded(value):
    with pytest.raises(CapabilityError, match="invalid_deadline"):
        OperationRequest("web.extract", {"url": "https://example.com"}, value)


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "https://user:password@example.com",
        "https://example.com:invalid",
        "https://example.com:0",
        "https://example.com:99999",
        "https://example.com/\n",
    ],
)
def test_non_http_or_credentialed_urls_are_rejected(url):
    with pytest.raises(CapabilityError, match="invalid_url"):
        validate_url(url)


def test_unknown_controls_fail_before_any_dispatch():
    request = OperationRequest(
        "web.extract", {"url": "https://example.com", "command": "anything"}
    )
    with pytest.raises(CapabilityError, match="invalid_input"):
        validate_request(request)


def test_paid_generation_requires_explicit_permission():
    request = OperationRequest(
        "speech.generate",
        {
            "provider": "elevenlabs",
            "text": "Hello",
            "voice": "test-voice",
            "language": "en-us",
        },
    )
    with pytest.raises(CapabilityError, match="payment_permission_required"):
        validate_request(request)


def test_kokoro_does_not_require_payment_permission():
    request = OperationRequest(
        "speech.generate",
        {
            "provider": "kokoro",
            "text": "Hello",
            "voice": "af_heart",
            "language": "en-us",
        },
    )
    assert validate_request(request)["id"] == "speech.generate"
