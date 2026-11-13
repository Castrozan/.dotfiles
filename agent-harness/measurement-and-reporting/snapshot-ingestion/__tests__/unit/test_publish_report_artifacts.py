import os
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import publish_report_artifacts as subject
from ingestion_snapshot_publisher import IngestionRefusedError

RUN_ID = "123456"
RUN_ATTEMPT = 2
REVISION = "a" * 40
ALLOWED_PREFIX = f"reports/overview/{RUN_ID}/{RUN_ATTEMPT}/"
ENVIRONMENT = {
    "INGEST_BASE_URL": "https://ingest.example.test",
    "INGEST_PRODUCER_SECRET": "test-secret",
}
LIMIT = subject.MAXIMUM_ARTIFACT_BYTE_LENGTH


def make_payload(run_identifier=RUN_ID, run_attempt=RUN_ATTEMPT):
    return {
        "workflow": {
            "repository": "Castrozan/.dotfiles",
            "revision": REVISION,
            "runId": run_identifier,
            "runAttempt": run_attempt,
        }
    }


def write_tree(root, files):
    for relative_path, body_bytes in files.items():
        target = Path(root, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body_bytes)
    return Path(root)


def publish(directory, object_key_prefix=ALLOWED_PREFIX, run_identifier=RUN_ID):
    return subject.publish_report_artifacts(
        make_payload(run_identifier), directory, object_key_prefix, ENVIRONMENT
    )


@contextmanager
def stubbed_collaborators(refused_environment=None, failing_object_keys=frozenset()):
    recorded = SimpleNamespace(environment_calls=[], publications=[])

    def stub_producing_environment(payload, environment):
        recorded.environment_calls.append(payload)
        if refused_environment is not None:
            raise refused_environment
        return {**environment, "PUBLICATION_MARKER": "stubbed", "GITHUB_RUN_ID": RUN_ID}

    def stub_publish_artifact(object_key, content_type, body_bytes, environment):
        if object_key in failing_object_keys:
            raise IngestionRefusedError(f"refused {object_key}")
        recorded.publications.append(
            SimpleNamespace(
                object_key=object_key,
                content_type=content_type,
                body_bytes=body_bytes,
                environment=environment,
            )
        )
        return {"objectKey": object_key, "byteLength": len(body_bytes)}

    with (
        patch.object(subject, "producing_environment", stub_producing_environment),
        patch.object(subject, "publish_artifact", stub_publish_artifact),
    ):
        yield recorded


def test_checks_producing_environment_before_scanning_or_publishing(tmp_path):
    directory = tmp_path / "empty"
    directory.mkdir()
    with stubbed_collaborators(
        refused_environment=IngestionRefusedError("identity refused")
    ) as recorded:
        with pytest.raises(IngestionRefusedError, match="identity refused"):
            publish(directory)
    assert recorded.environment_calls == [make_payload()]
    assert recorded.publications == []


@pytest.mark.parametrize("object_key_prefix", [ALLOWED_PREFIX, "reports/"])
def test_accepts_whitelisted_report_prefixes(tmp_path, object_key_prefix):
    directory = write_tree(tmp_path, {"index.html": b"<html>"})
    with stubbed_collaborators() as recorded:
        publish(directory, object_key_prefix)
    assert [publication.object_key for publication in recorded.publications] == [
        f"{object_key_prefix}index.html"
    ]


@pytest.mark.parametrize(
    "object_key_prefix",
    [
        "reports",
        "reports/overview/999/2/",
        "reports/overview/123456/3/",
        "reports/overview/123456/2",
        "other/",
        "/reports/",
    ],
)
def test_refuses_other_prefixes_before_publishing(tmp_path, object_key_prefix):
    directory = write_tree(tmp_path, {"index.html": b"<html>"})
    with stubbed_collaborators() as recorded:
        with pytest.raises(IngestionRefusedError):
            publish(directory, object_key_prefix)
    assert recorded.publications == []


def test_refuses_empty_tree_before_publishing(tmp_path):
    with stubbed_collaborators() as recorded:
        with pytest.raises(IngestionRefusedError, match="no files"):
            publish(write_tree(tmp_path, {}))
    assert recorded.publications == []


@pytest.mark.parametrize("special_entry_kind", ["symlink", "fifo"])
def test_refuses_symlink_and_special_entries_before_publishing(
    tmp_path, special_entry_kind
):
    directory = write_tree(tmp_path, {"index.html": b"<html>"})
    if special_entry_kind == "symlink":
        os.symlink(directory / "index.html", directory / "linked.html")
    else:
        os.mkfifo(directory / "pipe")
    with stubbed_collaborators() as recorded:
        with pytest.raises(IngestionRefusedError):
            publish(directory)
    assert recorded.publications == []


def test_accepts_exactly_the_request_limit_and_refuses_one_byte_more(tmp_path):
    accepted = write_tree(tmp_path / "accepted", {"index.html": b"x" * LIMIT})
    with stubbed_collaborators() as recorded:
        manifest = publish(accepted)
    assert manifest["artifacts"][0]["byteLength"] == LIMIT
    assert len(recorded.publications) == 1

    refused = write_tree(
        tmp_path / "refused", {"asset.css": b"a{}", "index.html": b"x" * (LIMIT + 1)}
    )
    with stubbed_collaborators() as recorded:
        with pytest.raises(IngestionRefusedError, match="request limit"):
            publish(refused)
    assert recorded.publications == []
