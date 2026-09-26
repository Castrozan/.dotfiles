import copy

import pytest

from ingestion_snapshot_publisher import IngestionRefusedError
from publish_quality_overview_snapshot import producing_environment


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
        "detailsBaseUrl": "https://storage.googleapis.com/zg-url-shortener-2026-dotfiles-usage-snapshots/reports/overview/123/2/",
    }


def test_event_source_identifies_measurement_run_instead_of_publisher_run(payload):
    original = {
        "GITHUB_SHA": "b" * 40,
        "GITHUB_RUN_ID": "999",
        "INGEST_PRODUCER_SECRET": "owned-fixture",
    }
    preserved = copy.deepcopy(original)
    environment = producing_environment(payload, original)
    assert environment["GITHUB_SHA"] == "a" * 40
    assert environment["GITHUB_RUN_ID"] == "123"
    assert environment["INGEST_PRODUCER_SECRET"] == "owned-fixture"
    assert original == preserved


@pytest.mark.parametrize(
    "section, key, value",
    [
        ("workflow", "revision", "b" * 40),
        ("workflow", "repository", "foreign/repository"),
        ("workflow", "runId", "../foreign"),
        ("workflow", "runAttempt", 0),
    ],
)
def test_invalid_source_identity_is_refused(payload, section, key, value):
    payload[section][key] = value
    with pytest.raises(IngestionRefusedError):
        producing_environment(payload, {})


def test_foreign_report_origin_is_refused(payload):
    payload["detailsBaseUrl"] = "https://example.test/123/2/"
    with pytest.raises(IngestionRefusedError):
        producing_environment(payload, {})
