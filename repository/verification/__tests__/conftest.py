import importlib.util
from pathlib import Path

import pytest

VERIFICATION_ROOT = Path(__file__).resolve().parents[1]
SUITE_MAP_SCRIPT = VERIFICATION_ROOT / "map-test-suite.py"


@pytest.fixture
def load_suite_map():
    def load():
        specification = importlib.util.spec_from_file_location(
            "suite_map", SUITE_MAP_SCRIPT
        )
        suite_map = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(suite_map)
        return suite_map

    return load
