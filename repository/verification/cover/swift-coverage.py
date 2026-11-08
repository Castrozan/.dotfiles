import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from swift_coverage_report import cobertura_coverage_xml
from swift_junit_report import SwiftSuiteOutcome, swift_junit_xml


REPOSITORY = Path(__file__).resolve().parents[3]
DESKTOP = Path("machine-configuration/desktop")
SWITCHER = DESKTOP / "window-management/workspace-window-switcher"
AMBIENT = DESKTOP / "appearance/screensaver/ambient-canvas"


def compile_test_binary(source_directories, entry_point, test_sources, binary):
    production_sources = sorted(
        path
        for source_directory in source_directories
        for path in (REPOSITORY / source_directory).rglob("*.swift")
        if path.name not in {entry_point, "Package.swift"}
        and "__tests__" not in path.parts
    )
    subprocess.run(
        [
            "xcrun",
            "swiftc",
            "-profile-generate",
            "-profile-coverage-mapping",
            "-o",
            str(binary),
            *map(str, production_sources),
            *map(str, test_sources),
        ],
        check=True,
        timeout=180,
    )


def _compile_coverage_suite(suite, directory, binaries, index):
    owner, entry_point, test_directory, _ = suite
    test_sources = sorted((REPOSITORY / owner / test_directory).rglob("*.swift"))
    if not test_sources:
        raise ValueError(f"No Swift tests found: {owner / test_directory}")
    binary = directory / f"suite-{index}"
    source_directories = [owner / "swift-sources"]
    if owner == SWITCHER:
        source_directories.append(DESKTOP / "input/command-sockets/swift-sources")
    compile_test_binary(source_directories, entry_point, test_sources, binary)
    binaries.append(binary)
    return binary


def _run_coverage_segment(binary, segment_count, directory, environment):
    arguments = []
    if segment_count is not None:
        manifest = directory / "loop.segments.json"
        manifest.write_text(
            json.dumps(
                {
                    "segments": [
                        {
                            "file": f"segment-{number}.mp4",
                            "durationSeconds": 30,
                        }
                        for number in range(segment_count)
                    ]
                }
            )
        )
        arguments.append(str(manifest))
    subprocess.run([str(binary), *arguments], env=environment, check=True, timeout=30)


def _suite_outcome_name(suite, segment_count):
    owner, _, test_directory, _ = suite
    name = f"{owner.name} {test_directory}"
    if segment_count is None:
        return name
    return f"{name} ({segment_count} segment{'' if segment_count == 1 else 's'})"


def _run_coverage_suite(suite, binary, directory, environment):
    outcomes = []
    for segment_count in suite[3] or (None,):
        started = time.monotonic()
        failure_message = None
        try:
            _run_coverage_segment(binary, segment_count, directory, environment)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            failure_message = str(error)
        outcomes.append(
            SwiftSuiteOutcome(
                _suite_outcome_name(suite, segment_count),
                time.monotonic() - started,
                failure_message,
            )
        )
    return outcomes


def _write_junit_report(outcomes):
    report_directory = Path(
        os.environ.get(
            "DOTFILES_TEST_REPORT_DIRECTORY", REPOSITORY / ".quality-results"
        )
    )
    report_directory.mkdir(parents=True, exist_ok=True)
    (report_directory / "swift-junit.xml").write_text(swift_junit_xml(outcomes) + "\n")
    failed = [outcome.name for outcome in outcomes if outcome.failure_message]
    if failed:
        raise SystemExit(f"Swift suites failed: {', '.join(failed)}")


def collect_coverage(output_directory):
    output_directory.mkdir(parents=True, exist_ok=True)
    suites = [
        (SWITCHER, "main.swift", "swift-sources/__tests__", ()),
        (AMBIENT, "ambient-canvas-player-main.swift", "__tests__/unit", ()),
        (AMBIENT, "ambient-canvas-player-main.swift", "__tests__/integration", (1, 2)),
    ]
    with tempfile.TemporaryDirectory(prefix="dotfiles-swift-coverage-") as temporary:
        directory = Path(temporary)
        environment = dict(
            os.environ, LLVM_PROFILE_FILE=str(directory / "%m-%p.profraw")
        )
        binaries = []
        outcomes = []
        for index, suite in enumerate(suites):
            binary = _compile_coverage_suite(
                suite,
                directory,
                binaries,
                index,
            )
            outcomes.extend(_run_coverage_suite(suite, binary, directory, environment))
        _write_junit_report(outcomes)
        profile = directory / "coverage.profdata"
        subprocess.run(
            [
                "xcrun",
                "llvm-profdata",
                "merge",
                "-sparse",
                *map(str, directory.glob("*.profraw")),
                "-o",
                str(profile),
            ],
            check=True,
            timeout=60,
        )
        objects = [
            argument for binary in binaries[1:] for argument in ("-object", str(binary))
        ]
        command = [
            "xcrun",
            "llvm-cov",
            "export",
            str(binaries[0]),
            *objects,
            f"-instr-profile={profile}",
            "-format=lcov",
        ]
        report = subprocess.run(
            command, check=True, capture_output=True, text=True, timeout=60
        ).stdout
        (output_directory / "swift-coverage.xml").write_text(
            cobertura_coverage_xml(report, REPOSITORY) + "\n"
        )
        subprocess.run(
            [
                "xcrun",
                "llvm-cov",
                "report",
                str(binaries[0]),
                *objects,
                f"-instr-profile={profile}",
            ],
            check=True,
            timeout=60,
        )


if __name__ == "__main__":
    collect_coverage(REPOSITORY / ".coverage-reports")
