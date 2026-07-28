from __future__ import annotations

import json

COMBINED_SNAPSHOTS_OBJECT_NAME = "aggregate/machine-usage-snapshots.json"


def machine_snapshot_prefix(snapshot_object_prefix: str) -> str:
    normalized_prefix = snapshot_object_prefix.strip("/")
    if not normalized_prefix:
        return ""
    return f"{normalized_prefix}/"


def read_machine_snapshots(
    storage_client, bucket_name: str, snapshot_object_prefix: str
) -> list[dict]:
    listed_blobs = storage_client.list_blobs(
        bucket_name,
        prefix=machine_snapshot_prefix(snapshot_object_prefix),
        delimiter="/",
    )
    return [
        json.loads(blob.download_as_text())
        for blob in listed_blobs
        if blob.name.endswith(".json")
    ]


def serialize_combined_snapshots(machine_snapshots: list[dict]) -> str:
    return json.dumps(machine_snapshots, indent=2, sort_keys=True) + "\n"


def publish_combined_snapshots(
    storage_client, bucket_name: str, snapshot_object_prefix: str
) -> str:
    machine_snapshots = read_machine_snapshots(
        storage_client, bucket_name, snapshot_object_prefix
    )
    blob = storage_client.bucket(bucket_name).blob(COMBINED_SNAPSHOTS_OBJECT_NAME)
    blob.cache_control = "no-cache"
    blob.upload_from_string(
        serialize_combined_snapshots(machine_snapshots),
        content_type="application/json",
    )
    return f"gs://{bucket_name}/{COMBINED_SNAPSHOTS_OBJECT_NAME}"
