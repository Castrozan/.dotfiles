from pathlib import Path
from xml.etree import ElementTree


def _coverage_source_file(line, repository, coverage):
    source = Path(line[3:]).resolve()
    if not source.is_relative_to(repository) or not source.is_file():
        raise ValueError(f"Invalid coverage source: {source}")
    relative_source = source.relative_to(repository)
    return (
        None
        if "__tests__" in relative_source.parts
        else ElementTree.SubElement(
            ElementTree.SubElement(
                coverage,
                "class",
                name=str(relative_source),
                filename=str(relative_source),
            ),
            "lines",
        )
    )


def _append_lcov_line(current_file, line):
    if current_file is None:
        return
    number, hits = line[3:].split(",")[:2]
    ElementTree.SubElement(
        current_file, "line", number=str(int(number)), hits=str(int(hits))
    )


def _populate_coverage_lines(lcov_report, repository, classes):
    current_file = None
    for line in lcov_report.splitlines():
        if line.startswith("SF:"):
            current_file = _coverage_source_file(line, repository, classes)
        elif line.startswith("DA:"):
            _append_lcov_line(current_file, line)
        elif line == "end_of_record":
            current_file = None


def cobertura_coverage_xml(lcov_report, repository):
    repository = repository.resolve()
    coverage = ElementTree.Element(
        "coverage", version="1", **{"line-rate": "0", "branch-rate": "0"}
    )
    sources = ElementTree.SubElement(coverage, "sources")
    ElementTree.SubElement(sources, "source").text = "."
    packages = ElementTree.SubElement(coverage, "packages")
    package = ElementTree.SubElement(packages, "package", name="swift")
    classes = ElementTree.SubElement(package, "classes")
    _populate_coverage_lines(lcov_report, repository, classes)
    lines = coverage.findall(".//line")
    covered_lines = sum(int(line.get("hits")) > 0 for line in lines)
    coverage.set("lines-valid", str(len(lines)))
    coverage.set("lines-covered", str(covered_lines))
    coverage.set("line-rate", str(covered_lines / len(lines) if lines else 0))
    return ElementTree.tostring(coverage, encoding="unicode")
