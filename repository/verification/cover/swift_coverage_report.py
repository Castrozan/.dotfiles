from pathlib import Path
from xml.etree import ElementTree


def sonar_coverage_xml(lcov_report, repository):
    repository = repository.resolve()
    coverage = ElementTree.Element("coverage", version="1")
    current_file = None
    for line in lcov_report.splitlines():
        if line.startswith("SF:"):
            source = Path(line[3:]).resolve()
            if not source.is_relative_to(repository) or not source.is_file():
                raise ValueError(f"Invalid coverage source: {source}")
            relative_source = source.relative_to(repository)
            current_file = (
                None
                if "__tests__" in relative_source.parts
                else ElementTree.SubElement(coverage, "file", path=str(relative_source))
            )
        elif line.startswith("DA:") and current_file is not None:
            number, hits = line[3:].split(",")[:2]
            ElementTree.SubElement(
                current_file,
                "lineToCover",
                lineNumber=str(int(number)),
                covered=str(int(hits) > 0).lower(),
            )
        elif line == "end_of_record":
            current_file = None
    return ElementTree.tostring(coverage, encoding="unicode")
