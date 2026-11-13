import json
import urllib.request

import pytest

import ingestion_snapshot_publisher
from ingestion_artifact_publisher import publish_artifact
from ingestion_snapshot_publisher import (
    IngestionRefusedError,
    publish_snapshot,
)

TEST_PRODUCER_CREDENTIAL = "producer-secret-under-test"
OBJECT_KEY = "snapshots/account-a1b2c3-kira.json"
RAW_BODY = b'{\n  "account_label": "account-a1b2c3"\n}\n'
UNICODE_BODY = '{"label": "conta-ção"}'.encode("utf-8")
NORMALIZED_EVENT = {"accountLabel": "account-a1b2c3"}


def build_environment(base_url):
    return {
        "INGEST_BASE_URL": base_url,
        "INGEST_PRODUCER_SECRET": TEST_PRODUCER_CREDENTIAL,
    }


def accepted_artifact_reply(object_key, body_bytes):
    acknowledgement = {"objectKey": object_key, "byteLength": len(body_bytes)}
    return json.dumps(acknowledgement).encode("utf-8")


def put_artifact(base_url, object_key=OBJECT_KEY, body_bytes=RAW_BODY):
    return publish_artifact(
        object_key,
        "application/json",
        body_bytes,
        build_environment(base_url),
    )


def publish_normalized_event(base_url):
    return publish_snapshot(
        "claude-usage",
        1,
        NORMALIZED_EVENT,
        "dotfiles-usage-exporter",
        build_environment(base_url),
    )


class TestTheArtifactIsPutAsExactBytesUnderItsEncodedKey:
    def test_sends_the_exact_bytes_to_the_percent_encoded_key_with_the_contract_headers(
        self, ingest_loopback, loopback_base_url
    ):
        ingest_loopback.reply_body = accepted_artifact_reply(OBJECT_KEY, RAW_BODY)

        acknowledgement = put_artifact(loopback_base_url)

        request = ingest_loopback.received_requests[0]
        assert request["method"] == "PUT"
        assert (
            request["path"] == "/ingest/artifacts/snapshots%2Faccount-a1b2c3-kira.json"
        )
        assert request["body"] == RAW_BODY
        assert request["headers"]["content-type"] == "application/json"
        assert request["headers"]["user-agent"] == "dotfiles-ingestion-publisher/1"
        assert (
            request["headers"]["x-ingest-producer-secret"] == TEST_PRODUCER_CREDENTIAL
        )
        assert acknowledgement == {"objectKey": OBJECT_KEY, "byteLength": len(RAW_BODY)}

    def test_percent_encodes_query_and_fragment_delimiters_in_an_opaque_key(
        self, ingest_loopback, loopback_base_url
    ):
        opaque_key = "snapshots/a?b#c d/%e"
        ingest_loopback.reply_body = accepted_artifact_reply(opaque_key, UNICODE_BODY)

        put_artifact(loopback_base_url, opaque_key, UNICODE_BODY)

        request = ingest_loopback.received_requests[0]
        assert request["path"] == "/ingest/artifacts/snapshots%2Fa%3Fb%23c%20d%2F%25e"
        assert request["body"] == UNICODE_BODY

    def test_uses_the_thirty_second_request_timeout(
        self, monkeypatch, ingest_loopback, loopback_base_url
    ):
        ingest_loopback.reply_body = accepted_artifact_reply(OBJECT_KEY, RAW_BODY)
        recorded_timeouts = []
        original_urlopen = urllib.request.urlopen

        def recording_urlopen(request, timeout=None, **keyword_arguments):
            recorded_timeouts.append(timeout)
            return original_urlopen(request, timeout=timeout, **keyword_arguments)

        monkeypatch.setattr(urllib.request, "urlopen", recording_urlopen)

        put_artifact(loopback_base_url)

        assert recorded_timeouts == [30]


class TestTheArtifactAcknowledgementIsRequiredAndWellFormed:
    def test_refuses_a_success_status_other_than_202(
        self, ingest_loopback, loopback_base_url
    ):
        ingest_loopback.reply_status = 200
        ingest_loopback.reply_body = accepted_artifact_reply(OBJECT_KEY, RAW_BODY)

        with pytest.raises(IngestionRefusedError, match="status 200"):
            put_artifact(loopback_base_url)

    def test_refuses_a_server_error_and_names_the_artifact_without_the_secret(
        self, ingest_loopback, loopback_base_url
    ):
        ingest_loopback.reply_status = 500
        ingest_loopback.reply_body = b'{"error": "storage unavailable"}'

        with pytest.raises(IngestionRefusedError) as refusal:
            put_artifact(loopback_base_url)

        message = str(refusal.value)
        assert "status 500" in message
        assert OBJECT_KEY in message
        assert TEST_PRODUCER_CREDENTIAL not in message

    @pytest.mark.parametrize(
        "reply_body, expected_reason",
        [
            (b"<html>accepted</html>", "no JSON object"),
            (b'["accepted"]', "no JSON object"),
            (
                json.dumps({"byteLength": len(RAW_BODY)}).encode(),
                "objectKey and byteLength",
            ),
            (
                json.dumps({"objectKey": OBJECT_KEY}).encode(),
                "objectKey and byteLength",
            ),
            (
                json.dumps(
                    {"objectKey": "snapshots/other.json", "byteLength": len(RAW_BODY)}
                ).encode(),
                "objectKey and byteLength",
            ),
            (
                json.dumps(
                    {"objectKey": OBJECT_KEY, "byteLength": len(RAW_BODY) + 1}
                ).encode(),
                "objectKey and byteLength",
            ),
        ],
    )
    def test_refuses_a_malformed_acknowledgement(
        self, ingest_loopback, loopback_base_url, reply_body, expected_reason
    ):
        ingest_loopback.reply_body = reply_body

        with pytest.raises(IngestionRefusedError, match=expected_reason):
            put_artifact(loopback_base_url)

    def test_refuses_without_any_request_when_the_producer_secret_is_not_seeded(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            ingestion_snapshot_publisher.urllib.request,
            "urlopen",
            lambda *unused, **ignored: pytest.fail("no request may be sent"),
        )

        with pytest.raises(IngestionRefusedError, match="INGEST_PRODUCER_SECRET"):
            publish_artifact(
                OBJECT_KEY,
                "application/json",
                RAW_BODY,
                {"INGEST_BASE_URL": "http://127.0.0.1:9/ingest"},
            )


class TestTheNormalizedEventPathSharesTheSameResponsePolicy:
    def test_refuses_an_event_acknowledgement_that_is_not_json(
        self, ingest_loopback, loopback_base_url
    ):
        ingest_loopback.reply_body = b"not json at all"

        with pytest.raises(IngestionRefusedError, match="claude-usage event"):
            publish_normalized_event(loopback_base_url)

    def test_refuses_an_event_status_other_than_202(
        self, ingest_loopback, loopback_base_url
    ):
        ingest_loopback.reply_status = 201
        ingest_loopback.reply_body = b"{}"

        with pytest.raises(IngestionRefusedError, match="status 201"):
            publish_normalized_event(loopback_base_url)
