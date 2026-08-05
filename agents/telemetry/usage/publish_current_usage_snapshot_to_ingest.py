from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from current_usage_snapshot import build_current_usage_snapshot  # noqa: E402
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

PUBLISHED_EXIT_CODE = 0
INGESTION_REFUSED_EXIT_CODE = 1


def publish_current_usage_snapshot(environment):
    usage_snapshot = build_current_usage_snapshot()
    if usage_snapshot is None:
        return None
    return publish_snapshot(
        CLAUDE_USAGE_TOPIC,
        CLAUDE_USAGE_SCHEMA_VERSION,
        build_claude_usage_payload(usage_snapshot),
        DEFAULT_PRODUCER_LABEL,
        environment,
    )


def main():
    try:
        acknowledgement = publish_current_usage_snapshot(os.environ)
    except IngestionRefusedError as refusal:
        print(refusal, file=sys.stderr)
        return INGESTION_REFUSED_EXIT_CODE
    if acknowledgement is None:
        print("this machine recorded no usage to publish")
        return PUBLISHED_EXIT_CODE
    print(json.dumps(acknowledgement))
    return PUBLISHED_EXIT_CODE


if __name__ == "__main__":
    sys.exit(main())
