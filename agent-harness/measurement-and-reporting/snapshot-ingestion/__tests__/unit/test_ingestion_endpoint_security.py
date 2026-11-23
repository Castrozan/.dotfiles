import urllib.request
from contextlib import nullcontext
from http.client import HTTPMessage
from io import BytesIO
from types import SimpleNamespace

import pytest

import ingestion_snapshot_publisher as publisher


def accepted_response():
    return nullcontext(SimpleNamespace(status=202, read=lambda: b"{}"))


@pytest.mark.parametrize(
    "endpoint",
    [
        "file:///local",
        "ftp://example.invalid/ingest",
        "http://remote.invalid/ingest",
        "https://user:password@example.invalid/ingest",
        "https://example.invalid/ingest#fragment",
        "https://example.invalid/ingest?query=1",
        "https://example.invalid:bad/ingest",
        " https://example.invalid/ingest",
    ],
)
def test_unsafe_ingestion_endpoints_are_refused_before_network(monkeypatch, endpoint):
    def must_not_send(*arguments, **keywords):
        raise AssertionError("invalid endpoint must not receive credentials")

    monkeypatch.setattr(publisher.urllib.request, "urlopen", must_not_send)
    with pytest.raises(publisher.IngestionRefusedError):
        publisher.post_ingestion_event(
            endpoint, "fixture-credential", {"topic": "claude-usage"}
        )


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://example.invalid/ingest",
        "http://127.0.0.1:9123/ingest",
        "http://localhost:9123/ingest",
        "http://[::1]:9123/ingest",
    ],
)
def test_https_and_explicit_loopback_endpoints_preserve_the_request(
    monkeypatch, endpoint
):
    requests = []

    def accepted(request, **keywords):
        requests.append(request)
        return accepted_response()

    monkeypatch.setattr(publisher.urllib.request, "urlopen", accepted)
    publisher.post_ingestion_event(
        endpoint, "fixture-credential", {"topic": "claude-usage"}
    )
    assert requests[0].full_url == endpoint + "/claude-usage"
    assert requests[0].get_header("X-ingest-producer-secret") == "fixture-credential"


def test_the_standard_redirect_handler_cannot_forward_the_producer_credential(
    monkeypatch,
):
    requests = []

    def accepted(request, **keywords):
        requests.append(request)
        return accepted_response()

    monkeypatch.setattr(publisher.urllib.request, "urlopen", accepted)
    publisher.post_ingestion_event(
        "https://example.invalid/ingest",
        "fixture-credential",
        {"topic": "claude-usage"},
    )
    redirected = urllib.request.HTTPRedirectHandler().redirect_request(
        requests[0],
        BytesIO(),
        302,
        "Found",
        HTTPMessage(),
        "https://different.invalid/target",
    )
    assert redirected is not None
    assert redirected.get_header("X-ingest-producer-secret") is None
    assert requests[0].get_header("X-ingest-producer-secret") == "fixture-credential"
