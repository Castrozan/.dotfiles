from pathlib import Path

import yaml

from instructions.instruction_surface_scanner import REPO_ROOT

SUITE_DIRECTORY = REPO_ROOT / "agent-harness" / "quality" / "evaluations" / "suites"


def suite_paths():
    return sorted(SUITE_DIRECTORY.rglob("*.yaml"))


def load_suite(suite_path: Path):
    return yaml.safe_load(suite_path.read_text())


def load_suite_cases(suite_name: str):
    return load_suite(next(SUITE_DIRECTORY.rglob(f"{suite_name}.yaml")))["casos"]


def every_authored_case():
    return [
        (suite_path, case)
        for suite_path in suite_paths()
        for case in load_suite(suite_path)["casos"]
    ]
