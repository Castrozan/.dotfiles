from dataclasses import dataclass
from xml.etree import ElementTree


@dataclass(frozen=True)
class SwiftSuiteOutcome:
    name: str
    duration_seconds: float
    failure_message: str | None = None


def swift_junit_xml(outcomes):
    failures = [outcome for outcome in outcomes if outcome.failure_message]
    suite = ElementTree.Element(
        "testsuite",
        name="swift",
        tests=str(len(outcomes)),
        failures=str(len(failures)),
        errors="0",
        time=f"{sum(outcome.duration_seconds for outcome in outcomes):.3f}",
    )
    for outcome in outcomes:
        case = ElementTree.SubElement(
            suite,
            "testcase",
            classname="swift",
            name=outcome.name,
            time=f"{outcome.duration_seconds:.3f}",
        )
        if outcome.failure_message:
            ElementTree.SubElement(case, "failure", message=outcome.failure_message)
    return ElementTree.tostring(suite, encoding="unicode", xml_declaration=True)
