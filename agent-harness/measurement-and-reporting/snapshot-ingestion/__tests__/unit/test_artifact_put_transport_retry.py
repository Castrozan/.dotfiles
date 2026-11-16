import urllib.error
from contextlib import nullcontext
from http.client import HTTPMessage
from io import BytesIO
from types import SimpleNamespace

import pytest

import ingestion_artifact_publisher as artifact_publisher
import ingestion_snapshot_publisher as snapshot_publisher

ACCEPTED_BODY = b'{"objectKey": "reports/overview/7/1/index.html", "byteLength": 3}'


def scripted_urlopen(monkeypatch, outcomes):
    calls = []

    def urlopen(*arguments, **keywords):
        calls.append(arguments)
        outcome = outcomes[len(calls) - 1]
        if isinstance(outcome, BaseException):
            raise outcome
        return nullcontext(SimpleNamespace(status=202, read=lambda: outcome))

    monkeypatch.setattr(snapshot_publisher.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(artifact_publisher.time, "sleep", lambda seconds: None)
    return calls


def put_index_artifact():
    return artifact_publisher.put_artifact(
        "https://lucaszanoni.com/ingest",
        "producer-secret-under-test",
        "reports/overview/7/1/index.html",
        "text/html",
        b"abc",
    )


@pytest.mark.parametrize(
    "transient_failure",
    [ConnectionResetError("connection reset"), TimeoutError("timed out")],
)
def test_a_transient_transport_failure_is_retried_until_accepted(
    monkeypatch, transient_failure
):
    calls = scripted_urlopen(monkeypatch, [transient_failure, ACCEPTED_BODY])

    acknowledgement = put_index_artifact()

    assert acknowledgement["byteLength"] == 3
    assert len(calls) == 2


def test_a_persistent_transport_failure_stops_after_the_bounded_attempts(
    monkeypatch,
):
    attempt_count = len(artifact_publisher.ARTIFACT_PUT_ATTEMPT_DELAYS_SECONDS)
    failures = [urllib.error.URLError("connection refused")] * attempt_count
    calls = scripted_urlopen(monkeypatch, failures)

    with pytest.raises(snapshot_publisher.IngestionTransportError) as raised:
        put_index_artifact()

    assert len(calls) == attempt_count
    assert "URLError" in str(raised.value)
    assert "producer-secret-under-test" not in str(raised.value)


def test_an_ingest_refusal_is_not_retried(monkeypatch):
    refusal = urllib.error.HTTPError(
        "https://lucaszanoni.com/ingest/artifacts/x",
        500,
        "failed",
        HTTPMessage(),
        BytesIO(b'{"error": "store failed"}'),
    )
    calls = scripted_urlopen(monkeypatch, [refusal])

    with pytest.raises(snapshot_publisher.IngestionRefusedError) as raised:
        put_index_artifact()

    assert not isinstance(raised.value, snapshot_publisher.IngestionTransportError)
    assert len(calls) == 1
