import copy

import pytest

from ingestion_snapshot_publisher import IngestionRefusedError
from publish_quality_overview_snapshot import producing_environment


PRIVATE_BASE_URL = "https://reports.example.test/private/reports/"
RETIRED_GCS_BASE_URL = (
    "https://storage.googleapis.com/"
    "zg-url-shortener-2026-dotfiles-usage-snapshots/reports/"
)


@pytest.fixture
def environment():
    return {"REPORT_ARTIFACT_BASE_URL": PRIVATE_BASE_URL}


@pytest.fixture
def payload():
    return {
        "workflow": {
            "repository": "Castrozan/.dotfiles",
            "revision": "a" * 40,
            "runId": "123",
            "runAttempt": 2,
        },
        "overview": {
            "subject": {"repository": "Castrozan/.dotfiles", "revision": "a" * 40}
        },
        "detailsBaseUrl": f"{PRIVATE_BASE_URL}overview/123/2/",
    }


def test_event_source_identifies_measurement_run_instead_of_publisher_run(
    payload, environment
):
    original = {
        "GITHUB_SHA": "b" * 40,
        "GITHUB_RUN_ID": "999",
        "INGEST_PRODUCER_SECRET": "owned-fixture",
        **environment,
    }
    preserved = copy.deepcopy(original)
    provenance = producing_environment(payload, original)
    assert provenance["GITHUB_SHA"] == "a" * 40
    assert provenance["GITHUB_RUN_ID"] == "123"
    assert provenance["INGEST_PRODUCER_SECRET"] == original["INGEST_PRODUCER_SECRET"]
    assert original == preserved


def test_private_attempt_details_url_is_derived_from_configured_origin(
    payload, environment
):
    assert payload["detailsBaseUrl"] == f"{PRIVATE_BASE_URL}overview/123/2/"
    provenance = producing_environment(payload, environment)
    assert provenance["REPORT_ARTIFACT_BASE_URL"] == PRIVATE_BASE_URL


@pytest.mark.parametrize(
    "section, key, value",
    [
        ("workflow", "revision", "b" * 40),
        ("workflow", "repository", "foreign/repository"),
        ("workflow", "runId", "../foreign"),
        ("workflow", "runId", " 123"),
        ("workflow", "runId", "0123"),
        ("workflow", "runAttempt", 0),
    ],
)
def test_invalid_source_identity_is_refused_without_repair(
    payload, environment, section, key, value
):
    payload[section][key] = value
    with pytest.raises(IngestionRefusedError):
        producing_environment(payload, environment)


def test_foreign_report_origin_is_refused(payload, environment):
    payload["detailsBaseUrl"] = "https://example.test/123/2/"
    with pytest.raises(IngestionRefusedError):
        producing_environment(payload, environment)


def test_retired_gcs_payload_origin_is_refused_against_configured_origin(
    payload, environment
):
    payload["detailsBaseUrl"] = f"{RETIRED_GCS_BASE_URL}overview/123/2/"
    with pytest.raises(IngestionRefusedError):
        producing_environment(payload, environment)


@pytest.mark.parametrize(
    "base_url",
    [
        "https://reports.example.test/private/reports/".replace("https://", ""),
        "http://reports.example.test/private/reports/",
        "https://reports.example.test/private/reports",
        "https://user:secret@reports.example.test/private/reports/",
        "https://@reports.example.test/private/reports/",
        "https://reports.example.test/private/reports/?token=1",
        "https://reports.example.test/private/reports/#fragment",
        "https://reports.example.test/private/reports/\n",
        "https://reports.example.test/private/ reports/",
        "https:///private/reports/",
    ],
)
def test_malformed_configured_base_url_is_refused(payload, base_url):
    payload["detailsBaseUrl"] = f"{base_url}overview/123/2/"
    with pytest.raises(IngestionRefusedError):
        producing_environment(payload, {"REPORT_ARTIFACT_BASE_URL": base_url})


def test_missing_configured_base_url_is_refused(payload):
    with pytest.raises(IngestionRefusedError):
        producing_environment(payload, {})


def test_empty_configured_base_url_is_refused(payload):
    with pytest.raises(IngestionRefusedError):
        producing_environment(payload, {"REPORT_ARTIFACT_BASE_URL": ""})
