from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from current_usage_snapshot import build_current_usage_snapshot  # noqa: E402
from usage_snapshot_writer import usage_snapshot_file_name  # noqa: E402

DEFAULT_SNAPSHOT_OBJECT_PREFIX = "snapshots/"


def snapshot_object_name(snapshot_object_prefix: str, usage_snapshot: dict) -> str:
    file_name = usage_snapshot_file_name(
        usage_snapshot["account_label"], usage_snapshot["machine_label"]
    )
    normalized_prefix = snapshot_object_prefix.strip("/")
    if not normalized_prefix:
        return file_name
    return f"{normalized_prefix}/{file_name}"


def serialize_usage_snapshot(usage_snapshot: dict) -> str:
    return json.dumps(usage_snapshot, indent=2, sort_keys=True) + "\n"


def upload_usage_snapshot(bucket_name: str, snapshot_object_prefix: str) -> str:
    from google.cloud import storage

    usage_snapshot = build_current_usage_snapshot()
    if usage_snapshot is None:
        return ""
    object_name = snapshot_object_name(snapshot_object_prefix, usage_snapshot)
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.cache_control = "no-cache"
    blob.upload_from_string(
        serialize_usage_snapshot(usage_snapshot),
        content_type="application/json",
    )
    return f"gs://{bucket_name}/{object_name}"


def main() -> int:
    bucket_name = os.environ.get("USAGE_SNAPSHOT_BUCKET")
    if not bucket_name:
        print(
            "USAGE_SNAPSHOT_BUCKET is not set; nothing uploaded",
            file=sys.stderr,
        )
        return 1
    snapshot_object_prefix = os.environ.get(
        "USAGE_SNAPSHOT_OBJECT_PREFIX", DEFAULT_SNAPSHOT_OBJECT_PREFIX
    )
    uploaded_uri = upload_usage_snapshot(bucket_name, snapshot_object_prefix)
    if not uploaded_uri:
        print(
            "no current Claude account in ~/.claude.json; nothing uploaded",
            file=sys.stderr,
        )
        return 0
    print(f"uploaded {uploaded_uri}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
