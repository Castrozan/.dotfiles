import json
import os
from pathlib import Path
import re
import sys

from ingestion_snapshot_publisher import IngestionRefusedError, publish_snapshot


TOPIC = "dotfiles-quality-overview"
REPOSITORY = "Castrozan/.dotfiles"
REPORT_BASE_URL = (
    "https://storage.googleapis.com/"
    "zg-url-shortener-2026-dotfiles-usage-snapshots/reports/overview"
)


def _validate_producing_repository(workflow, subject):
    if workflow["repository"] != REPOSITORY or subject["repository"] != REPOSITORY:
        raise IngestionRefusedError("Overview repository differs from the producer")


def _validate_producing_revision(subject, revision):
    if not re.fullmatch(r"[a-f0-9]{40}", revision) or subject["revision"] != revision:
        raise IngestionRefusedError("Overview revision differs from the producing run")


def _validate_producing_attempt(identifier, attempt):
    if (
        not re.fullmatch(r"[1-9]\d*", identifier, flags=re.ASCII)
        or not isinstance(attempt, int)
        or attempt < 1
    ):
        raise IngestionRefusedError(
            "Overview run and attempt must identify GitHub execution"
        )


def producing_environment(payload, environment):
    workflow = payload["workflow"]
    subject = payload["overview"]["subject"]
    revision = workflow["revision"]
    identifier = workflow["runId"]
    attempt = workflow["runAttempt"]
    _validate_producing_repository(workflow, subject)
    _validate_producing_revision(subject, revision)
    _validate_producing_attempt(identifier, attempt)
    if payload["detailsBaseUrl"] != f"{REPORT_BASE_URL}/{identifier}/{attempt}/":
        raise IngestionRefusedError(
            "Overview details do not identify the producing attempt"
        )
    return {
        **environment,
        "GITHUB_REPOSITORY": REPOSITORY,
        "GITHUB_SHA": revision,
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_RUN_ID": identifier,
    }


def main():
    try:
        payload = json.loads(Path(".quality-results/overview/payload.json").read_text())
        environment = producing_environment(payload, os.environ)
        acknowledgement = publish_snapshot(
            TOPIC,
            1,
            payload,
            "dotfiles-quality-overview-publisher",
            environment,
        )
    except (IngestionRefusedError, KeyError, ValueError) as refusal:
        print(refusal, file=sys.stderr)
        return 1
    print(json.dumps(acknowledgement))
    return 0


if __name__ == "__main__":
    sys.exit(main())
