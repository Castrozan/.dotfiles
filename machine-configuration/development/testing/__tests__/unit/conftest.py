import nightly_deep_test_tiers
import pytest


@pytest.fixture
def keep_the_log_and_the_steward_inbox_off_the_live_machine(tmp_path, monkeypatch):
    monkeypatch.setattr(
        nightly_deep_test_tiers, "LOG_DIRECTORY", tmp_path / "nightly-log"
    )
    monkeypatch.setenv("STEWARD_WORKSPACE_DIR", str(tmp_path / "no-steward-here"))
