import argparse
from contextlib import chdir
from itertools import chain
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ElementTree

import coverage
from defusedxml.common import DefusedXmlException
from native_junit import native_test_suites, write_test_suites


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
EXPECTED_SHARDS = (("unit", 0, 1), ("integration", 0, 2), ("integration", 1, 2))


def validate_producing_attempts(producing_attempts):
    if len(producing_attempts) != len(EXPECTED_SHARDS):
        raise ValueError("Python evidence requires exactly three producing attempts")
    if min(producing_attempts) < 1:
        raise ValueError("Python producing attempts must be positive")


def unexpected_shard_artifacts(source, producing_attempts):
    expected_names = {
        f"python-shard-{tier}-{index}-{run_attempt}"
        for (tier, index, _), run_attempt in zip(
            EXPECTED_SHARDS, producing_attempts, strict=True
        )
    }
    return [
        f"Unexpected Python shard artifact: {path.name}"
        for path in sorted(source.glob("python-shard-*"))
        if path.name not in expected_names
    ]


def read_shard_report(artifact, shard, output, case_identities):
    tier, index, count = shard
    report = (
        artifact / ".quality-results" / f"pytest-{tier}-shard-{index}-of-{count}.xml"
    )
    diagnostic = output / ".quality-results" / "shard-diagnostics" / artifact.name
    diagnostic.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(report, diagnostic / report.name)
    if list(report.parent.glob("pytest-*.xml")) != [report]:
        raise ValueError(f"Duplicate or foreign native shard reports: {artifact}")
    suites, identities = native_test_suites(report)
    if case_identities.intersection(identities):
        raise ValueError(f"Test case collision across Python shards: {report}")
    case_identities.update(identities)
    return suites


def write_complete_tier_reports(tier_reports, output):
    for tier, reports in tier_reports.items():
        expected_count = sum(shard_tier == tier for shard_tier, _, _ in EXPECTED_SHARDS)
        if len(reports) != expected_count:
            continue
        write_test_suites(
            chain.from_iterable(reports),
            output / ".quality-results" / f"pytest-{tier}.xml",
        )


def collect_shard_reports(source, output, producing_attempts):
    unexpected_artifacts = unexpected_shard_artifacts(source, producing_attempts)
    errors = list(unexpected_artifacts)
    tier_reports = {"unit": [], "integration": []}
    case_identities = set()
    coverage_paths = []
    for shard, run_attempt in zip(EXPECTED_SHARDS, producing_attempts, strict=True):
        tier, index, _ = shard
        artifact = source / f"python-shard-{tier}-{index}-{run_attempt}"
        measurement = artifact / ".coverage-reports" / f".coverage.{tier}-{index}"
        try:
            suites = read_shard_report(artifact, shard, output, case_identities)
            tier_reports[tier].append(suites)
        except (
            OSError,
            ValueError,
            ElementTree.ParseError,
            DefusedXmlException,
        ) as error:
            errors.append(str(error))
        if measurement.is_file():
            coverage_paths.append(measurement.resolve())
        else:
            errors.append(f"Missing Python coverage shard: {measurement}")
    if unexpected_artifacts:
        return errors, coverage_paths
    write_complete_tier_reports(tier_reports, output)
    return errors, coverage_paths


def combine_coverage(coverage_paths, output):
    branch_modes = set()
    for path in coverage_paths:
        measurement = coverage.CoverageData(basename=str(path))
        measurement.read()
        if not measurement.measured_files():
            raise ValueError(f"Empty Python coverage shard: {path}")
        branch_modes.add(measurement.has_arcs())
    if len(branch_modes) != 1:
        raise ValueError("Python coverage shards use incompatible branch settings")
    configuration = REPOSITORY_ROOT / "repository/verification/cover/coverage.ini"
    with chdir(REPOSITORY_ROOT):
        combined = coverage.Coverage(
            config_file=str(configuration),
            data_file=str(output / ".coverage-reports" / ".coverage"),
        )
        combined.combine(
            data_paths=list(map(str, coverage_paths)), strict=True, keep=True
        )
        combined.save()
        combined.xml_report(
            outfile=str(output / ".coverage-reports" / "python-coverage.xml")
        )


def merge_python_evidence(source, output, producing_attempts):
    validate_producing_attempts(producing_attempts)
    source, output = Path(source).resolve(), Path(output).resolve()
    for directory in (".quality-results", ".coverage-reports"):
        (output / directory).mkdir(parents=True, exist_ok=True)
    for report in (
        ".quality-results/pytest-unit.xml",
        ".quality-results/pytest-integration.xml",
        ".coverage-reports/.coverage",
        ".coverage-reports/python-coverage.xml",
    ):
        (output / report).unlink(missing_ok=True)
    errors, coverage_paths = collect_shard_reports(source, output, producing_attempts)
    if errors:
        return errors
    try:
        combine_coverage(coverage_paths, output)
    except (OSError, ValueError, coverage.exceptions.CoverageException) as error:
        (output / ".coverage-reports/python-coverage.xml").unlink(missing_ok=True)
        errors.append(str(error))
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("unit_attempt", type=int)
    parser.add_argument("integration_first_attempt", type=int)
    parser.add_argument("integration_second_attempt", type=int)
    arguments = parser.parse_args()
    producing_attempts = (
        arguments.unit_attempt,
        arguments.integration_first_attempt,
        arguments.integration_second_attempt,
    )
    if min(producing_attempts) < 1:
        parser.error("Python producing attempts must be positive")
    errors = merge_python_evidence(
        arguments.source, arguments.output, producing_attempts
    )
    for error in errors:
        print(error, file=sys.stderr)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
