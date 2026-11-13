from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ccusage_daily_reader import CcusageCollectionError  # noqa: E402
from current_usage_snapshot import build_current_usage_snapshot  # noqa: E402
from ingestion_artifact_publisher import publish_artifact  # noqa: E402
from ingestion_snapshot_publisher import (  # noqa: E402
    IngestionRefusedError,
    publish_snapshot,
)
from publish_claude_usage_snapshot import (  # noqa: E402
    CLAUDE_USAGE_SCHEMA_VERSION,
    CLAUDE_USAGE_TOPIC,
    DEFAULT_PRODUCER_LABEL,
    build_claude_usage_payload,
)
from usage_snapshot_writer import usage_snapshot_file_name  # noqa: E402

PUBLISHED_EXIT_CODE = 0
PUBLISH_FAILED_EXIT_CODE = 1
RAW_ARTIFACT_CONTENT_TYPE = "application/json"
SNAPSHOT_OBJECT_KEY_PREFIX = "snapshots/"


def encode_raw_usage_snapshot(usage_snapshot):
    return (json.dumps(usage_snapshot, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_raw_usage_snapshot_object_key(usage_snapshot):
    snapshot_file_name = usage_snapshot_file_name(
        usage_snapshot["account_label"], usage_snapshot["machine_label"]
    )
    return f"{SNAPSHOT_OBJECT_KEY_PREFIX}{snapshot_file_name}"


def publish_current_usage_snapshot(environment):
    usage_snapshot = build_current_usage_snapshot()
    if usage_snapshot is None:
        return None
    normalized_payload = build_claude_usage_payload(usage_snapshot)
    raw_object_key = build_raw_usage_snapshot_object_key(usage_snapshot)
    raw_body = encode_raw_usage_snapshot(usage_snapshot)
    snapshot_acknowledgement = publish_snapshot(
        CLAUDE_USAGE_TOPIC,
        CLAUDE_USAGE_SCHEMA_VERSION,
        normalized_payload,
        DEFAULT_PRODUCER_LABEL,
        environment,
    )
    artifact_acknowledgement = publish_artifact(
        raw_object_key, RAW_ARTIFACT_CONTENT_TYPE, raw_body, environment
    )
    return {
        "snapshot": snapshot_acknowledgement,
        "artifact": artifact_acknowledgement,
    }


def main():
    try:
        acknowledgement = publish_current_usage_snapshot(os.environ)
    except (IngestionRefusedError, CcusageCollectionError) as failure:
        print(failure, file=sys.stderr)
        return PUBLISH_FAILED_EXIT_CODE
    if acknowledgement is None:
        print("this machine recorded no usage to publish")
        return PUBLISHED_EXIT_CODE
    print(json.dumps(acknowledgement))
    return PUBLISHED_EXIT_CODE


if __name__ == "__main__":
    sys.exit(main())
