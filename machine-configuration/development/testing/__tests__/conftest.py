import sys
from pathlib import Path

import pytest

CAPABILITY_DIRECTORY = Path(__file__).resolve().parent.parent
SCRIPTS_DIRECTORY = CAPABILITY_DIRECTORY / "scripts"
REPOSITORY_ROOT = CAPABILITY_DIRECTORY.parents[2]

sys.path.insert(0, str(SCRIPTS_DIRECTORY))
sys.path.insert(0, str(SCRIPTS_DIRECTORY / "lib"))


@pytest.fixture
def repository_root() -> Path:
    return REPOSITORY_ROOT
