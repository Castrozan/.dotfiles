import sys
from pathlib import Path

SKILL_DIRECTORY = Path(__file__).resolve().parents[2]
WAIT_GUARD_MODULES_DIRECTORY = (
    SKILL_DIRECTORY.parents[3] / "hooks" / "runtime" / "pre-tool-use" / "common"
)

for importable_directory in (
    SKILL_DIRECTORY / "scripts",
    WAIT_GUARD_MODULES_DIRECTORY,
    Path(__file__).resolve().parent,
):
    sys.path.insert(0, str(importable_directory))
