import importlib.util
import sys
from pathlib import Path
from defusedxml import ElementTree


MODULE_PATH = Path(__file__).resolve().parents[3] / "cover/swift_junit_report.py"
specification = importlib.util.spec_from_file_location("swift_junit_report", MODULE_PATH)
reporting = importlib.util.module_from_spec(specification)
sys.modules["swift_junit_report"] = reporting
specification.loader.exec_module(reporting)


def test_records_each_suite_run_with_its_failure():
    document = ElementTree.fromstring(
        reporting.swift_junit_xml(
            [
                reporting.SwiftSuiteOutcome("switcher swift-sources/__tests__", 1.25),
                reporting.SwiftSuiteOutcome(
                    "ambient-canvas __tests__/integration (2 segments)",
                    0.5,
                    "Command returned non-zero exit status 1.",
                ),
            ]
        )
    )
    assert document.attrib == {
        "name": "swift",
        "tests": "2",
        "failures": "1",
        "errors": "0",
        "time": "1.750",
    }
    cases = document.findall("testcase")
    assert [case.get("name") for case in cases] == [
        "switcher swift-sources/__tests__",
        "ambient-canvas __tests__/integration (2 segments)",
    ]
    assert cases[0].find("failure") is None
    assert cases[1].find("failure").get("message") == (
        "Command returned non-zero exit status 1."
    )


def test_escapes_names_and_messages():
    xml = reporting.swift_junit_xml(
        [reporting.SwiftSuiteOutcome('a & <b> "c"', 0.0, "x < y & z")]
    )
    case = ElementTree.fromstring(xml).find("testcase")
    assert case.get("name") == 'a & <b> "c"'
    assert case.find("failure").get("message") == "x < y & z"
