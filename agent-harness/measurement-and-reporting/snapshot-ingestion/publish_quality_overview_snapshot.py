import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from ingestion_snapshot_publisher import IngestionRefusedError, publish_snapshot


TOPIC = "dotfiles-quality-overview"
REPOSITORY = "Castrozan/.dotfiles"


def _validate_producing_repository(workflow, subject):
    if workflow["repository"] != REPOSITORY or subject["repository"] != REPOSITORY:
        raise IngestionRefusedError("Overview repository differs from the producer")


def _validate_producing_revision(subject, revision):
    if not re.fullmatch(r"[a-f0-9]{40}", revision) or subject["revision"] != revision:
        raise IngestionRefusedError("Overview revision differs from the producing run")


def _validate_producing_attempt(identifier, attempt):
    if (
        not re.fullmatch(r"[1-9]\d*", identifier, flags=re.ASCII)
        or type(attempt) is not int
        or attempt < 1
    ):
        raise IngestionRefusedError(
            "Overview run and attempt must identify GitHub execution"
        )


def _has_report_base_url_shape(value):
    return (
        isinstance(value, str) and value.startswith("https://") and value.endswith("/")
    )


def _is_forbidden_base_url_character(character):
    return ord(character) <= 32 or ord(character) == 127 or character in "\\?#"


def _has_usable_report_authority(base_url):
    try:
        authority = urlsplit(base_url)
        return (
            bool(authority.hostname)
            and "@" not in authority.netloc
            and authority.port != 0
        )
    except ValueError:
        return False


def _configured_report_artifact_base_url(environment):
    base_url = environment.get("REPORT_ARTIFACT_BASE_URL")
    if (
        not _has_report_base_url_shape(base_url)
        or any(_is_forbidden_base_url_character(character) for character in base_url)
        or not _has_usable_report_authority(base_url)
    ):
        raise IngestionRefusedError(
            "REPORT_ARTIFACT_BASE_URL must be credential-free HTTPS ending in a slash"
        )
    return base_url


def producing_environment(payload, environment):
    workflow = payload["workflow"]
    subject = payload["overview"]["subject"]
    revision = workflow["revision"]
    identifier = workflow["runId"]
    attempt = workflow["runAttempt"]
    _validate_producing_repository(workflow, subject)
    _validate_producing_revision(subject, revision)
    _validate_producing_attempt(identifier, attempt)
    base_url = _configured_report_artifact_base_url(environment)
    if payload["detailsBaseUrl"] != f"{base_url}overview/{identifier}/{attempt}/":
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
