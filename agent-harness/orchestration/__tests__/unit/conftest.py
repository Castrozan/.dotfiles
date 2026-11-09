import pytest
from orchestration_test_support import notifications as notifications


@pytest.fixture(autouse=True)
def isolated_state_home(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
