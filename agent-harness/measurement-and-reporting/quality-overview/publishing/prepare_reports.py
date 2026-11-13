import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil

from artifact_selection import ARTIFACT_PRODUCERS


@dataclass(frozen=True)
class VerifiedCoverageSources:
    coverage_directory: Path
    shared_assets_directory: Path


def validate_coverage_selection(selection):
    if type(selection.get("id")) is not int or selection["id"] < 1:
        raise ValueError("A verified coverage artifact is required")
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", selection.get("digest", "")):
        raise ValueError("Coverage artifact has no verified digest")
    producer = selection.get("producer", {})
    if producer.get("jobName") != ARTIFACT_PRODUCERS["coverage-report"][0]:
        raise ValueError("Coverage artifact has no verified producing job")


def verified_shared_assets(artifact_directory):
    shared = artifact_directory / "data"
    if shared.is_symlink() or not shared.is_dir():
        raise ValueError("Verified coverage artifact has no shared assets directory")
    stylesheet = shared / "bcov.css"
    if stylesheet.is_symlink() or not stylesheet.is_file():
        raise ValueError("Verified coverage artifact has no shared stylesheet")
    return shared


def verified_coverage(context, downloads):
    validate_coverage_selection(context["artifacts"]["coverage-report"])
    artifact_directory = downloads / "coverage-report"
    coverage = artifact_directory / "bats"
    if not (coverage / "coverage.json").is_file():
        raise ValueError("Verified coverage artifact has no coverage document")
    if not (coverage / "index.html").is_file():
        raise ValueError("Verified coverage artifact has no coverage HTML document")
    return VerifiedCoverageSources(coverage, verified_shared_assets(artifact_directory))


def prepare_reports(context, downloads, site):
    sources = verified_coverage(context, downloads)
    site.mkdir(parents=True, exist_ok=True)
    shutil.copytree(sources.coverage_directory, site / "coverage")
    shutil.copytree(sources.shared_assets_directory, site / "data")


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
