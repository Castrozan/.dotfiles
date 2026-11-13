import urllib.error
import urllib.request
from contextlib import nullcontext
from http.client import HTTPMessage
from io import BytesIO
from types import SimpleNamespace

import pytest

import ingestion_snapshot_publisher as publisher


def test_error_response_read_timeout_is_an_explicit_refusal(monkeypatch):
    class TimeoutBody(BytesIO):
        def read(self, *arguments, **keywords):
            raise TimeoutError("error body timed out")

    def refused(*arguments, **keywords):
        raise urllib.error.HTTPError(
            "https://example.invalid/ingest/claude-usage",
            500,
            "failed",
            HTTPMessage(),
            TimeoutBody(),
        )

    monkeypatch.setattr(publisher.urllib.request, "urlopen", refused)
    request = urllib.request.Request("https://example.invalid/ingest/claude-usage")
    with pytest.raises(publisher.IngestionRefusedError):
        publisher.send_ingest_request(request, "claude-usage event")


def test_invalid_response_encoding_is_an_explicit_refusal(monkeypatch):
    monkeypatch.setattr(
        publisher.urllib.request,
        "urlopen",
        lambda *arguments, **keywords: nullcontext(
            SimpleNamespace(status=202, read=lambda: b"\xff")
        ),
    )
    request = urllib.request.Request("https://example.invalid/ingest/claude-usage")
    with pytest.raises(publisher.IngestionRefusedError):
        publisher.send_ingest_request(request, "claude-usage event")


@pytest.mark.parametrize(
    "failure",
    [
        urllib.error.URLError("connection refused"),
        TimeoutError("timed out"),
        ConnectionResetError("connection reset"),
    ],
)
def test_unreachable_ingest_is_an_explicit_refusal(monkeypatch, failure):
    def unreachable(*arguments, **keywords):
        raise failure

    monkeypatch.setattr(publisher.urllib.request, "urlopen", unreachable)
    request = urllib.request.Request("https://example.invalid/ingest/claude-usage")
    with pytest.raises(publisher.IngestionRefusedError):
        publisher.send_ingest_request(request, "claude-usage event")


def test_response_read_timeout_is_an_explicit_refusal(monkeypatch):
    def timeout_read():
        raise TimeoutError("response body timed out")

    def opened(*arguments, **keywords):
        return nullcontext(SimpleNamespace(status=202, read=timeout_read))

    monkeypatch.setattr(publisher.urllib.request, "urlopen", opened)
    request = urllib.request.Request("https://example.invalid/ingest/claude-usage")
    with pytest.raises(publisher.IngestionRefusedError):
        publisher.send_ingest_request(request, "claude-usage event")
