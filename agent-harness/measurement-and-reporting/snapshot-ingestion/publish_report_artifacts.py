import hashlib
import json
import mimetypes
import os
import sys
from pathlib import Path, PurePosixPath

from ingestion_artifact_publisher import publish_artifact
from ingestion_snapshot_publisher import IngestionRefusedError
from publish_quality_overview_snapshot import producing_environment
from report_artifact_sources import (
    MAXIMUM_ARTIFACT_BYTE_LENGTH,
    collect_artifact_sources,
    require_within_request_limit,
)

DEFAULT_CONTENT_TYPE = "application/octet-stream"
ENTRYPOINT_FILE_NAME = "index.html"
REPORTS_OBJECT_KEY_PREFIX = "reports/"
OVERVIEW_REPORTS_OBJECT_KEY_PREFIX = "reports/overview/"
WORKFLOW_IDENTITY_FIELDS = ("repository", "revision", "runId", "runAttempt")


def require_allowed_object_key_prefix(payload, object_key_prefix):
    workflow = payload["workflow"]
    overview_prefix = (
        f"{OVERVIEW_REPORTS_OBJECT_KEY_PREFIX}"
        f"{workflow['runId']}/{workflow['runAttempt']}/"
    )
    if object_key_prefix not in (REPORTS_OBJECT_KEY_PREFIX, overview_prefix):
        raise IngestionRefusedError(
            "Report artifact prefix must be the producing run's overview prefix or reports/"
        )


def order_for_publication(sources):
    return sorted(
        sources,
        key=lambda source: (
            PurePosixPath(source.relative_path).name == ENTRYPOINT_FILE_NAME,
            source.relative_path,
        ),
    )


def content_type_for(relative_path):
    content_type, _content_encoding = mimetypes.guess_type(relative_path)
    return content_type or DEFAULT_CONTENT_TYPE


def read_artifact_body(source):
    with source.file_path.open("rb") as body_stream:
        body_bytes = body_stream.read(MAXIMUM_ARTIFACT_BYTE_LENGTH + 1)
    require_within_request_limit(source.relative_path, len(body_bytes))
    observed = (len(body_bytes), hashlib.sha256(body_bytes).hexdigest())
    if observed != (source.byte_length, source.sha256):
        raise IngestionRefusedError("Report artifact changed after preflight")
    return body_bytes


def publish_sources_in_order(sources, object_key_prefix, environment):
    artifacts = []
    for source in order_for_publication(sources):
        object_key = f"{object_key_prefix}{source.relative_path}"
        content_type = content_type_for(source.relative_path)
        body_bytes = read_artifact_body(source)
        publish_artifact(object_key, content_type, body_bytes, environment)
        artifacts.append(
            {
                "objectKey": object_key,
                "byteLength": len(body_bytes),
                "sha256": hashlib.sha256(body_bytes).hexdigest(),
                "contentType": content_type,
            }
        )
    return artifacts


def publish_report_artifacts(payload, directory, object_key_prefix, environment):
    publication_environment = producing_environment(payload, environment)
    require_allowed_object_key_prefix(payload, object_key_prefix)
    sources = collect_artifact_sources(directory, object_key_prefix)
    artifacts = publish_sources_in_order(
        sources, object_key_prefix, publication_environment
    )
    return {
        "workflow": {
            field: payload["workflow"][field] for field in WORKFLOW_IDENTITY_FIELDS
        },
        "artifacts": artifacts,
    }


def main(arguments):
    try:
        payload_path, source_directory, object_key_prefix = arguments
        manifest = publish_report_artifacts(
            json.loads(Path(payload_path).read_text(encoding="utf-8")),
            Path(source_directory),
            object_key_prefix,
            os.environ,
        )
    except (IngestionRefusedError, KeyError, OSError, TypeError, ValueError) as refusal:
        print(refusal, file=sys.stderr)
        return 1
    print(json.dumps(manifest))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
