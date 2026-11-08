import importlib.util
import subprocess
import sys
from pathlib import Path
from defusedxml import ElementTree

import pytest


COVER_DIRECTORY = Path(__file__).resolve().parents[3] / "cover"
sys.path.insert(0, str(COVER_DIRECTORY))
specification = importlib.util.spec_from_file_location(
    "swift_coverage", COVER_DIRECTORY / "swift-coverage.py"
)
swift_coverage = importlib.util.module_from_spec(specification)
specification.loader.exec_module(swift_coverage)


def test_records_every_segment_and_fails_after_writing_the_report(
    monkeypatch, tmp_path
):
    def run_segment(binary, segment_count, directory, environment):
        if segment_count == 2:
            raise subprocess.CalledProcessError(1, [str(binary)])

    monkeypatch.setattr(swift_coverage, "_run_coverage_segment", run_segment)
    monkeypatch.setenv("DOTFILES_TEST_REPORT_DIRECTORY", str(tmp_path))
    suite = (Path("desktop/ambient-canvas"), "main.swift", "__tests__/integration", (1, 2))

    outcomes = swift_coverage._run_coverage_suite(suite, Path("binary"), tmp_path, {})
    with pytest.raises(SystemExit, match="ambient-canvas __tests__/integration \\(2 segments\\)"):
        swift_coverage._write_junit_report(outcomes)

    document = ElementTree.parse(tmp_path / "swift-junit.xml").getroot()
    assert document.get("tests") == "2"
    assert document.get("failures") == "1"
    assert [case.get("name") for case in document.findall("testcase")] == [
        "ambient-canvas __tests__/integration (1 segment)",
        "ambient-canvas __tests__/integration (2 segments)",
    ]


def test_passing_suites_write_the_report_without_failing(monkeypatch, tmp_path):
    monkeypatch.setattr(swift_coverage, "_run_coverage_segment", lambda *arguments: None)
    monkeypatch.setenv("DOTFILES_TEST_REPORT_DIRECTORY", str(tmp_path))
    suite = (Path("desktop/switcher"), "main.swift", "swift-sources/__tests__", ())

    swift_coverage._write_junit_report(
        swift_coverage._run_coverage_suite(suite, Path("binary"), tmp_path, {})
    )

    document = ElementTree.parse(tmp_path / "swift-junit.xml").getroot()
    assert document.get("failures") == "0"
    assert document.find("testcase").get("name") == "switcher swift-sources/__tests__"
