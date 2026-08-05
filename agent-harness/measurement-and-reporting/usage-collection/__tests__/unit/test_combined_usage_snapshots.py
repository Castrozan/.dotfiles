from __future__ import annotations

import json

from combined_usage_snapshots import (
    COMBINED_SNAPSHOTS_OBJECT_NAME,
    publish_combined_snapshots,
    read_machine_snapshots,
    serialize_combined_snapshots,
)


class FakeBlob:
    def __init__(self, name: str, payload: str = ""):
        self.name = name
        self.payload = payload
        self.cache_control = None
        self.uploaded_content_type = None

    def download_as_text(self) -> str:
        return self.payload

    def upload_from_string(self, data: str, content_type: str) -> None:
        self.payload = data
        self.uploaded_content_type = content_type


class FakeBucket:
    def __init__(self, blobs_by_name: dict):
        self.blobs_by_name = blobs_by_name

    def blob(self, name: str) -> FakeBlob:
        return self.blobs_by_name.setdefault(name, FakeBlob(name))


class FakeStorageClient:
    def __init__(self, blobs_by_name: dict):
        self.blobs_by_name = blobs_by_name
        self.listing_calls = []

    def list_blobs(self, bucket_name: str, prefix: str, delimiter: str):
        self.listing_calls.append(
            {"bucket": bucket_name, "prefix": prefix, "delimiter": delimiter}
        )
        return [
            blob
            for name, blob in self.blobs_by_name.items()
            if name.startswith(prefix) and "/" not in name[len(prefix) :]
        ]

    def bucket(self, bucket_name: str) -> FakeBucket:
        return FakeBucket(self.blobs_by_name)


def build_storage_client_with_two_machines() -> FakeStorageClient:
    return FakeStorageClient(
        {
            "snapshots/owner-kira.json": FakeBlob(
                "snapshots/owner-kira.json",
                json.dumps({"machine_label": "kira"}),
            ),
            "snapshots/owner-chise.json": FakeBlob(
                "snapshots/owner-chise.json",
                json.dumps({"machine_label": "chise"}),
            ),
            "snapshots/claude-usage/events/one.json": FakeBlob(
                "snapshots/claude-usage/events/one.json",
                json.dumps({"unreadable": True}),
            ),
        }
    )


def test_reads_only_the_machine_snapshots_beside_the_prefix():
    storage_client = build_storage_client_with_two_machines()

    machine_snapshots = read_machine_snapshots(
        storage_client, "usage-bucket", "snapshots/"
    )

    assert sorted(snapshot["machine_label"] for snapshot in machine_snapshots) == [
        "chise",
        "kira",
    ]


def test_lists_with_a_delimiter_so_nested_event_objects_stay_out():
    storage_client = build_storage_client_with_two_machines()

    read_machine_snapshots(storage_client, "usage-bucket", "snapshots/")

    assert storage_client.listing_calls == [
        {"bucket": "usage-bucket", "prefix": "snapshots/", "delimiter": "/"}
    ]


def test_publishes_every_machine_snapshot_as_one_json_array():
    storage_client = build_storage_client_with_two_machines()

    published_uri = publish_combined_snapshots(
        storage_client, "usage-bucket", "snapshots/"
    )

    combined_blob = storage_client.blobs_by_name[COMBINED_SNAPSHOTS_OBJECT_NAME]
    combined_snapshots = json.loads(combined_blob.payload)
    assert published_uri == f"gs://usage-bucket/{COMBINED_SNAPSHOTS_OBJECT_NAME}"
    assert len(combined_snapshots) == 2
    assert combined_blob.uploaded_content_type == "application/json"
    assert combined_blob.cache_control == "no-cache"


def test_serializes_an_empty_bucket_as_an_empty_array():
    assert json.loads(serialize_combined_snapshots([])) == []
