import importlib.util
from pathlib import Path
from xml.etree import ElementTree

import pytest


MODULE_PATH = Path(__file__).resolve().parents[3] / "cover/swift_coverage_report.py"
specification = importlib.util.spec_from_file_location(
    "swift_coverage_report", MODULE_PATH
)
reporting = importlib.util.module_from_spec(specification)
specification.loader.exec_module(reporting)


def test_preserves_measured_lines_with_portable_paths_and_xml_escaping(tmp_path):
    source = tmp_path / "Sources/Player & Window.swift"
    source.parent.mkdir()
    source.write_text("first\nsecond\nthird\n")
    report = f"SF:{source}\nDA:1,0\nDA:3,1200\nLF:2\nLH:1\nend_of_record\n"

    root = ElementTree.fromstring(reporting.sonar_coverage_xml(report, tmp_path))

    assert root.tag == "coverage"
    assert root.attrib == {"version": "1"}
    files = root.findall("file")
    assert len(files) == 1
    assert files[0].get("path") == "Sources/Player & Window.swift"
    assert [line.attrib for line in files[0]] == [
        {"lineNumber": "1", "covered": "false"},
        {"lineNumber": "3", "covered": "true"},
    ]


def test_omits_test_sources_from_production_coverage(tmp_path):
    source = tmp_path / "__tests__/unit/PlayerTests.swift"
    source.parent.mkdir(parents=True)
    source.write_text("test\n")
    report = f"SF:{source}\nDA:1,1\nend_of_record\n"

    root = ElementTree.fromstring(reporting.sonar_coverage_xml(report, tmp_path))

    assert root.findall("file") == []


@pytest.mark.parametrize("filename", ["../outside.swift", "missing.swift"])
def test_rejects_sources_outside_the_checkout_or_missing_from_it(tmp_path, filename):
    report = f"SF:{tmp_path / filename}\nDA:1,1\nend_of_record\n"

    with pytest.raises(ValueError, match="coverage source"):
        reporting.sonar_coverage_xml(report, tmp_path)
