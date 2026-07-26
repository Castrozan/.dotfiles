import sys
from datetime import datetime, timezone
from pathlib import Path

from ingestion_snapshot_publisher import (
    IngestionRefusedError,
    run_snapshot_publisher,
)

DOTFILES_TEST_COVERAGE_TOPIC = "dotfiles-test-coverage"
DOTFILES_TEST_COVERAGE_SCHEMA_VERSION = 1
DEFAULT_PRODUCER_LABEL = "dotfiles-shell-coverage"
MISSING_DOCUMENT_ARGUMENT_EXIT_CODE = 2
KCOV_NAIVE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
COVERAGE_RATE_DECIMAL_PLACES = 4


def stamp_naive_kcov_date_as_utc(kcov_date):
    recorded_at = datetime.strptime(kcov_date, KCOV_NAIVE_DATE_FORMAT).replace(
        tzinfo=timezone.utc
    )
    return recorded_at.isoformat().replace("+00:00", "Z")


def compute_line_coverage_rate(covered_lines, measurable_lines):
    return round(covered_lines / measurable_lines, COVERAGE_RATE_DECIMAL_PLACES)


def resolve_repository_relative_path(measured_file, checkout_root):
    try:
        return str(Path(measured_file).relative_to(checkout_root))
    except ValueError as unmappable:
        raise IngestionRefusedError(
            f"kcov measured {measured_file} outside the checkout at {checkout_root} "
            "so it cannot be reported as a repository path"
        ) from unmappable


def build_measured_file_result(file_document, checkout_root):
    covered_lines = int(file_document["covered_lines"])
    measurable_lines = int(file_document["total_lines"])
    return {
        "path": resolve_repository_relative_path(file_document["file"], checkout_root),
        "coveredLines": covered_lines,
        "measurableLines": measurable_lines,
        "lineCoverageRate": compute_line_coverage_rate(covered_lines, measurable_lines),
    }


def resolve_checkout_root(environment):
    return Path(
        environment.get("GITHUB_WORKSPACE") or Path(__file__).resolve().parents[2]
    )


def build_test_coverage_payload(coverage_document, environment):
    checkout_root = resolve_checkout_root(environment)
    covered_lines = int(coverage_document["covered_lines"])
    measurable_lines = int(coverage_document["total_lines"])
    commit = environment.get("GITHUB_SHA")
    if not commit:
        raise IngestionRefusedError(
            "GITHUB_SHA must name the commit the coverage run measured"
        )
    return {
        "recordedAt": stamp_naive_kcov_date_as_utc(coverage_document["date"]),
        "commit": commit,
        "coveredLines": covered_lines,
        "measurableLines": measurable_lines,
        "lineCoverageRate": compute_line_coverage_rate(covered_lines, measurable_lines),
        "files": [
            build_measured_file_result(file_document, checkout_root)
            for file_document in coverage_document["files"]
            if int(file_document["total_lines"]) > 0
        ],
    }


def main(command_line_arguments):
    if not command_line_arguments:
        print(
            "the kcov coverage.json path must be given because kcov names its "
            "output directory after a hash that changes every run",
            file=sys.stderr,
        )
        return MISSING_DOCUMENT_ARGUMENT_EXIT_CODE
    return run_snapshot_publisher(
        DOTFILES_TEST_COVERAGE_TOPIC,
        DOTFILES_TEST_COVERAGE_SCHEMA_VERSION,
        DEFAULT_PRODUCER_LABEL,
        build_test_coverage_payload,
        command_line_arguments[0],
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
