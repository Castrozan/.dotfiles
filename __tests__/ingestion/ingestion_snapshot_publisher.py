import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PRODUCER_SECRET_HEADER_NAME = "x-ingest-producer-secret"
ACCEPTED_INGEST_STATUS_CODE = 202
INGEST_REQUEST_TIMEOUT_SECONDS = 30


class IngestionRefusedError(RuntimeError):
    pass


def read_current_produced_at():
    stamped_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    return stamped_at.replace("+00:00", "Z")


def resolve_event_source(environment):
    repository = environment.get("GITHUB_REPOSITORY")
    commit = environment.get("GITHUB_SHA")
    if not repository or not commit:
        return None

    event_source = {"repository": repository, "commit": commit}
    server_url = environment.get("GITHUB_SERVER_URL")
    run_identifier = environment.get("GITHUB_RUN_ID")
    if server_url and run_identifier:
        event_source["runUrl"] = (
            f"{server_url}/{repository}/actions/runs/{run_identifier}"
        )
    return event_source


def build_ingestion_event(topic, schema_version, payload, producer_label, event_source):
    ingestion_event = {
        "topic": topic,
        "schemaVersion": schema_version,
        "producedAt": read_current_produced_at(),
        "producer": producer_label,
        "payload": payload,
    }
    if event_source is not None:
        ingestion_event["source"] = event_source
    return ingestion_event


def build_topic_endpoint_url(ingest_base_url, topic):
    return f"{ingest_base_url.rstrip('/')}/{topic}"


def describe_ingest_refusal(topic, status_code, response_body):
    try:
        reported_error = json.loads(response_body).get("error", response_body)
    except json.JSONDecodeError:
        reported_error = response_body
    return (
        f"the ingest api refused the {topic} event "
        f"with status {status_code}: {reported_error}"
    )


def post_ingestion_event(ingest_base_url, producer_secret, ingestion_event):
    topic = ingestion_event["topic"]
    request = urllib.request.Request(
        url=build_topic_endpoint_url(ingest_base_url, topic),
        data=json.dumps(ingestion_event).encode("utf-8"),
        headers={
            "content-type": "application/json",
            PRODUCER_SECRET_HEADER_NAME: producer_secret,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request, timeout=INGEST_REQUEST_TIMEOUT_SECONDS
        ) as response:
            status_code = response.status
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as refusal:
        raise IngestionRefusedError(
            describe_ingest_refusal(topic, refusal.code, refusal.read().decode("utf-8"))
        ) from refusal

    if status_code != ACCEPTED_INGEST_STATUS_CODE:
        raise IngestionRefusedError(
            describe_ingest_refusal(topic, status_code, response_body)
        )
    return json.loads(response_body)


def read_required_environment_value(environment, variable_name, purpose):
    value = environment.get(variable_name)
    if not value:
        raise IngestionRefusedError(f"{variable_name} must {purpose}")
    return value


def publish_snapshot(
    topic, schema_version, payload, default_producer_label, environment
):
    ingest_base_url = read_required_environment_value(
        environment, "INGEST_BASE_URL", "name the ingest api mount the event is sent to"
    )
    producer_secret = read_required_environment_value(
        environment,
        "INGEST_PRODUCER_SECRET",
        "carry the secret the ingest api accepts producers by",
    )
    ingestion_event = build_ingestion_event(
        topic,
        schema_version,
        payload,
        environment.get("INGEST_PRODUCER_LABEL") or default_producer_label,
        resolve_event_source(environment),
    )
    return post_ingestion_event(ingest_base_url, producer_secret, ingestion_event)


def run_snapshot_publisher(
    topic, schema_version, default_producer_label, build_payload, source_document_path
):
    try:
        source_document = json.loads(Path(source_document_path).read_text())
        acknowledgement = publish_snapshot(
            topic,
            schema_version,
            build_payload(source_document, os.environ),
            default_producer_label,
            os.environ,
        )
    except IngestionRefusedError as refusal:
        print(refusal, file=sys.stderr)
        return 1
    print(json.dumps(acknowledgement))
    return 0
