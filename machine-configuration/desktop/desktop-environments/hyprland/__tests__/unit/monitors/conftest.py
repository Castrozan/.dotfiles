import monitor_configuration
import pytest


@pytest.fixture
def monitor_state_files(tmp_path, monkeypatch):
    monkeypatch.setattr(monitor_configuration, "MONITORS_CONF", tmp_path / "none.conf")
    monkeypatch.setattr(
        monitor_configuration, "OVERRIDE_FILE", tmp_path / "override.conf"
    )
    monkeypatch.setattr(monitor_configuration, "DISPLAY_MODE_FILE", tmp_path / "mode")
    monkeypatch.setattr(
        monitor_configuration, "RECONCILE_LOCK_FILE", tmp_path / "reconcile.lock"
    )
    return tmp_path
