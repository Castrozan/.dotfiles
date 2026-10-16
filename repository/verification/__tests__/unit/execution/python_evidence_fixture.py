from contextlib import chdir
import importlib.util
from pathlib import Path
import runpy
import sys
import xml.etree.ElementTree as ElementTree

import coverage
from defusedxml import ElementTree as DefusedElementTree


MODULE_PATH = (
    Path(__file__).resolve().parents[3] / "runner/python/merge-python-evidence.py"
)
sys.path.insert(0, str(MODULE_PATH.parent))
SPECIFICATION = importlib.util.spec_from_file_location(
    "merge_python_evidence", MODULE_PATH
)
MERGER = importlib.util.module_from_spec(SPECIFICATION)
SPECIFICATION.loader.exec_module(MERGER)


def read_xml(path):
    return DefusedElementTree.parse(path).getroot()


def create_evidence(tmp_path, monkeypatch):
    repository = tmp_path / "checkout"
    for directory in (
        "agent-harness",
        "machine-configuration",
        "repository/verification/cover",
    ):
        (repository / directory).mkdir(parents=True)
    configuration = repository / "repository/verification/cover/coverage.ini"
    configuration.write_text(
        (
            MERGER.REPOSITORY_ROOT / "repository/verification/cover/coverage.ini"
        ).read_text()
    )
    source = repository / "repository/owned.py"
    source.write_text("if selected:\n    result = 'yes'\nelse:\n    result = 'no'\n")
    monkeypatch.setattr(MERGER, "REPOSITORY_ROOT", repository)
    artifacts = tmp_path / "artifacts"
    for tier, index, count in MERGER.EXPECTED_SHARDS:
        artifact = artifacts / f"python-shard-{tier}-{index}-2"
        reports = artifact / ".quality-results"
        measurements = artifact / ".coverage-reports"
        reports.mkdir(parents=True)
        measurements.mkdir()
        suite = ElementTree.Element(
            "testsuite",
            name="pytest",
            tests="3",
            failures="1",
            errors="0",
            skipped="1",
            time="0.123",
            timestamp="2026-10-16T00:01:00Z",
        )
        properties = ElementTree.SubElement(suite, "properties")
        ElementTree.SubElement(
            properties, "property", name="shard", value=f"{tier}-{index}"
        )
        for name, outcome in (
            ("pass", None),
            ("failure", "failure"),
            ("skip", "skipped"),
        ):
            case = ElementTree.SubElement(
                suite,
                "testcase",
                classname=f"owned.{tier}.{index}",
                name=name,
                time="0.001",
            )
            if outcome:
                ElementTree.SubElement(
                    case, outcome, message="native outcome"
                ).text = "owned details"
            ElementTree.SubElement(case, "system-out").text = "native stdout"
        root = ElementTree.Element("testsuites")
        root.append(suite)
        ElementTree.ElementTree(root).write(
            reports / f"pytest-{tier}-shard-{index}-of-{count}.xml"
        )
        with chdir(repository):
            measurement = coverage.Coverage(
                config_file=str(configuration),
                branch=True,
                data_suffix=False,
                data_file=str(measurements / f".coverage.{tier}-{index}"),
            )
            measurement.start()
            runpy.run_path(str(source), init_globals={"selected": index == 0})
            measurement.stop()
            measurement.save()
    return artifacts, tmp_path / "output", source
