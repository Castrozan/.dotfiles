import runpy
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def plugin_root(tmp_path_factory):
    helper = Path(__file__).resolve().parents[1] / "wellput_fixture.py"
    return runpy.run_path(str(helper))["export_plugin_fixture"](
        tmp_path_factory.mktemp("wellput")
    )
