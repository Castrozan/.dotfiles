import hashlib
import json
from string import ascii_letters
from urllib.parse import unquote, urlsplit
from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st

import ingestion_snapshot_publisher as transport
from ingestion_snapshot_publisher import IngestionRefusedError
from publish_quality_overview_snapshot import REPOSITORY, producing_environment
from publish_report_artifacts import publish_report_artifacts

PRIVATE_BASE_URL = "https://reports.example.test/private/reports/"


def payload_for(attempt=2, base_url=PRIVATE_BASE_URL):
    workflow = {
        "repository": REPOSITORY,
        "revision": "a" * 40,
        "runId": "123",
        "runAttempt": attempt,
    }
    return {
        "workflow": workflow,
        "overview": {"subject": {"repository": REPOSITORY, "revision": "a" * 40}},
        "detailsBaseUrl": f"{base_url}overview/123/{attempt}/",
    }


@pytest.mark.parametrize("prefix", ["reports/", "reports/overview/123/2/"])
def test_real_provenance_and_artifact_adapter_join(tmp_path, monkeypatch, prefix):
    environment = {
        "REPORT_ARTIFACT_BASE_URL": PRIVATE_BASE_URL,
        "INGEST_BASE_URL": "https://ingest.example.test/ingest",
        "INGEST_PRODUCER_SECRET": uuid4().hex,
        "GITHUB_SHA": "b" * 40,
        "GITHUB_RUN_ID": "999",
    }
    files = {"index.html": b"<html></html>", "données.json": b"{}"}
    for relative_path, body in files.items():
        (tmp_path / relative_path).write_bytes(body)
    requests = []

    def acknowledge(request):
        requests.append(request)
        object_key = unquote(urlsplit(request.full_url).path.split("/artifacts/", 1)[1])
        return 202, json.dumps(
            {"objectKey": object_key, "byteLength": len(request.data)}
        )

    monkeypatch.setattr(transport, "read_ingest_response", acknowledge)
    manifest = publish_report_artifacts(payload_for(), tmp_path, prefix, environment)
    assert manifest["workflow"] == payload_for()["workflow"]
    assert [item["objectKey"] for item in manifest["artifacts"]][
        -1
    ] == f"{prefix}index.html"
    for request, item in zip(requests, manifest["artifacts"], strict=True):
        assert request.get_method() == "PUT"
        assert (
            request.get_header("X-ingest-producer-secret")
            == environment["INGEST_PRODUCER_SECRET"]
        )
        assert "X-ingest-producer-secret" not in request.headers
        assert request.data == files[item["objectKey"].removeprefix(prefix)]
        assert item["byteLength"] == len(request.data)
        assert item["sha256"] == hashlib.sha256(request.data).hexdigest()
    assert environment["GITHUB_SHA"] == "b" * 40
    assert environment["GITHUB_RUN_ID"] == "999"


@given(
    port=st.one_of(
        st.integers(min_value=65536, max_value=10**9).map(str),
        st.text(alphabet=ascii_letters, min_size=1, max_size=12),
    )
)
def test_invalid_url_ports_are_refused_without_normalization(port):
    base_url = f"https://reports.example.test:{port}/private/reports/"
    with pytest.raises(IngestionRefusedError):
        producing_environment(
            payload_for(base_url=base_url), {"REPORT_ARTIFACT_BASE_URL": base_url}
        )


@given(attempt=st.one_of(st.booleans(), st.none(), st.text(), st.floats()))
def test_non_integer_attempts_are_not_producing_identities(attempt):
    with pytest.raises(IngestionRefusedError):
        producing_environment(
            payload_for(attempt), {"REPORT_ARTIFACT_BASE_URL": PRIVATE_BASE_URL}
        )


@pytest.mark.parametrize(
    "base_url",
    [
        "https://[invalid]/reports/",
        "https://reports.example.test:0/reports/",
        "https://reports.example.test/\\reports/",
    ],
)
def test_unusable_base_urls_are_refused_before_publication(base_url):
    with pytest.raises(IngestionRefusedError):
        producing_environment(
            payload_for(base_url=base_url), {"REPORT_ARTIFACT_BASE_URL": base_url}
        )
