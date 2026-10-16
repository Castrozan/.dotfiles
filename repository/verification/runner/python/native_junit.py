import xml.etree.ElementTree as ElementTree

from defusedxml import ElementTree as DefusedElementTree


def suites_from_root(root, report):
    if root.tag == "testsuite":
        return [root]
    if root.tag != "testsuites":
        raise ValueError(f"Malformed native JUnit report: {report}")
    if any(child.tag != "testsuite" for child in root):
        raise ValueError(f"Malformed native JUnit report: {report}")
    return list(root)


def case_identity(case):
    if case.get("name"):
        return case.get("classname", ""), case.get("name")
    if any(
        case.find(outcome) is not None for outcome in ("failure", "error", "skipped")
    ):
        return None
    raise ValueError("Unnamed native JUnit case has no outcome")


def native_test_suites(report):
    root = DefusedElementTree.parse(report, forbid_dtd=True).getroot()
    suites = suites_from_root(root, report)
    cases = []
    for suite in suites:
        cases.extend(suite.iter("testcase"))
    if not cases:
        raise ValueError(f"Empty native JUnit report: {report}")
    identities = {case_identity(case) for case in cases}
    identities.discard(None)
    return suites, identities


def write_test_suites(suites, destination):
    root = ElementTree.Element("testsuites")
    root.extend(suites)
    ElementTree.ElementTree(root).write(
        destination, encoding="utf-8", xml_declaration=True
    )
