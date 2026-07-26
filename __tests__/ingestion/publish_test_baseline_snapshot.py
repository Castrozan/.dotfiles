import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DOTFILES_TEST_BASELINE_TOPIC = "dotfiles-test-baseline"
DOTFILES_TEST_BASELINE_SCHEMA_VERSION = 1
PRODUCER_SECRET_HEADER_NAME = "x-ingest-producer-secret"
ACCEPTED_INGEST_STATUS_CODE = 202
DEFAULT_PRODUCER_LABEL = "dotfiles-agent-evals"
DEFAULT_BASELINE_DOCUMENT_PATH = Path(__file__).resolve().parent / "baseline.json"
INGEST_REQUEST_TIMEOUT_SECONDS = 30


class IngestionRefusedError(RuntimeError):
    pass


def build_category_result(category_name, category_document):
    return {
        "category": category_name,
        "passed": category_document["passed"],
        "failed": category_document["failed"],
        "tests": [
            {"name": test["name"], "passed": test["passed"]}
            for test in category_document["tests"]
        ],
    }


def build_test_baseline_payload(baseline_document):
    categories = baseline_document["categories"]
    return {
        "recordedAt": baseline_document["generated_at"],
        "commit": baseline_document["git_commit"],
        "totalTests": baseline_document["total_tests"],
        "passedTests": baseline_document["total_passed"],
        "failedTests": baseline_document["total_failed"],
        "passRate": baseline_document["pass_rate"],
        "categories": [
            build_category_result(category_name, categories[category_name])
            for category_name in sorted(categories)
        ],
    }


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


def build_ingestion_event(baseline_document, producer_label, event_source):
    ingestion_event = {
        "topic": DOTFILES_TEST_BASELINE_TOPIC,
        "schemaVersion": DOTFILES_TEST_BASELINE_SCHEMA_VERSION,
        "producedAt": read_current_produced_at(),
        "producer": producer_label,
        "payload": build_test_baseline_payload(baseline_document),
    }
    if event_source is not None:
        ingestion_event["source"] = event_source
    return ingestion_event


def build_topic_endpoint_url(ingest_base_url, topic):
    return f"{ingest_base_url.rstrip('/')}/{topic}"


def describe_ingest_refusal(status_code, response_body):
    try:
        reported_error = json.loads(response_body).get("error", response_body)
    except json.JSONDecodeError:
        reported_error = response_body
    return (
        f"the ingest api refused the {DOTFILES_TEST_BASELINE_TOPIC} event "
        f"with status {status_code}: {reported_error}"
    )


def post_ingestion_event(ingest_base_url, producer_secret, ingestion_event):
    request = urllib.request.Request(
        url=build_topic_endpoint_url(ingest_base_url, ingestion_event["topic"]),
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
            describe_ingest_refusal(refusal.code, refusal.read().decode("utf-8"))
        ) from refusal

    if status_code != ACCEPTED_INGEST_STATUS_CODE:
        raise IngestionRefusedError(describe_ingest_refusal(status_code, response_body))
    return json.loads(response_body)


def read_required_environment_value(environment, variable_name, purpose):
    value = environment.get(variable_name)
    if not value:
        raise IngestionRefusedError(f"{variable_name} must {purpose}")
    return value


def publish_test_baseline_snapshot(baseline_document_path, environment):
    ingest_base_url = read_required_environment_value(
        environment, "INGEST_BASE_URL", "name the ingest api mount the event is sent to"
    )
    producer_secret = read_required_environment_value(
        environment,
        "INGEST_PRODUCER_SECRET",
        "carry the secret the ingest api accepts producers by",
    )
    baseline_document = json.loads(Path(baseline_document_path).read_text())
    ingestion_event = build_ingestion_event(
        baseline_document,
        environment.get("INGEST_PRODUCER_LABEL") or DEFAULT_PRODUCER_LABEL,
        resolve_event_source(environment),
    )
    return post_ingestion_event(ingest_base_url, producer_secret, ingestion_event)


def main(command_line_arguments):
    baseline_document_path = (
        command_line_arguments[0]
        if command_line_arguments
        else DEFAULT_BASELINE_DOCUMENT_PATH
    )
    try:
        acknowledgement = publish_test_baseline_snapshot(
            baseline_document_path, os.environ
        )
    except IngestionRefusedError as refusal:
        print(refusal, file=sys.stderr)
        return 1
    print(json.dumps(acknowledgement))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
