import sys
from pathlib import Path

A2A_CLI_PACKAGE_PARENT_DIRECTORY = Path(__file__).resolve().parents[1] / "scripts"
AGENT_HARNESS_DIRECTORY = Path(__file__).resolve().parents[3]
for importable_directory in (
    A2A_CLI_PACKAGE_PARENT_DIRECTORY,
    AGENT_HARNESS_DIRECTORY / "servants",
    AGENT_HARNESS_DIRECTORY / "hooks" / "runtime" / "common",
):
    sys.path.insert(0, str(importable_directory))
