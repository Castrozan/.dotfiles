import argparse
import json
from pathlib import Path
import re
import shutil

from artifact_selection import ARTIFACT_PRODUCERS


def validate_coverage_selection(selection):
    if type(selection.get("id")) is not int or selection["id"] < 1:
        raise ValueError("A verified coverage artifact is required")
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", selection.get("digest", "")):
        raise ValueError("Coverage artifact has no verified digest")
    producer = selection.get("producer", {})
    if producer.get("jobName") != ARTIFACT_PRODUCERS["coverage-report"][0]:
        raise ValueError("Coverage artifact has no verified producing job")


def verified_coverage(context, downloads):
    validate_coverage_selection(context["artifacts"]["coverage-report"])
    coverage = downloads / "coverage-report"
    if not (coverage / "bats/coverage.json").is_file():
        raise ValueError("Verified coverage artifact has no coverage document")
    return coverage


def prepare_reports(context, downloads, site):
    coverage = verified_coverage(context, downloads)
    site.mkdir(parents=True, exist_ok=True)
    shutil.copytree(coverage, site / "coverage")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("context", type=Path)
    parser.add_argument("downloads", type=Path)
    parser.add_argument("site", type=Path)
    arguments = parser.parse_args()
    prepare_reports(
        json.loads(arguments.context.read_text()),
        arguments.downloads,
        arguments.site,
    )


if __name__ == "__main__":
    main()
