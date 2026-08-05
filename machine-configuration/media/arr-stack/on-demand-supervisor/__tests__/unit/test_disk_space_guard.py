import json
import sys
from pathlib import Path

SUPERVISOR_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "on_demand_supervisor"
)
sys.path.insert(0, str(SUPERVISOR_PACKAGE_DIRECTORY_PATH))

import disk_space_guard
import supervisor_core

ON_DEMAND_SERVICES = ["radarr", "sonarr", "prowlarr", "qbittorrent", "bazarr"]


def disk_guard_config(tmp_path, warning=30, critical=15):
    return {
        "path": str(tmp_path),
        "warning_gigabytes": warning,
        "critical_gigabytes": critical,
        "fill_service": "qbittorrent",
        "critical_reminder_seconds": 21600,
        "alert_state_file": str(tmp_path / "alert-state.json"),
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_username": "",
        "email_sender": "",
        "email_recipient": "",
        "app_password_file": "",
    }


def test_classify_free_space_thresholds():
    assert disk_space_guard.classify_free_space(10, 30, 15) == "critical"
    assert disk_space_guard.classify_free_space(20, 30, 15) == "warning"
    assert disk_space_guard.classify_free_space(40, 30, 15) == "ok"


def test_alert_is_due_only_on_transition_or_critical_reminder():
    ok_state = {"level": "ok", "last_alert_epoch": 0.0}
    assert disk_space_guard.alert_is_due("critical", ok_state, 1000.0, 21600) is True
    critical_state = {"level": "critical", "last_alert_epoch": 1000.0}
    assert (
        disk_space_guard.alert_is_due("critical", critical_state, 1100.0, 21600)
        is False
    )
    assert (
        disk_space_guard.alert_is_due("critical", critical_state, 1000.0 + 21600, 21600)
        is True
    )
    warning_state = {"level": "warning", "last_alert_epoch": 1000.0}
    assert (
        disk_space_guard.alert_is_due("warning", warning_state, 9_000_000.0, 21600)
        is False
    )
    assert disk_space_guard.alert_is_due("ok", critical_state, 2000.0, 21600) is True


def test_enforce_critical_stops_fill_service_alerts_and_persists(tmp_path, monkeypatch):
    stopped = []
    alerts = []
    monkeypatch.setattr(disk_space_guard, "free_gigabytes_available", lambda path: 5.0)
    monkeypatch.setattr(
        disk_space_guard,
        "stop_on_demand_services",
        lambda base, services, dry_run: stopped.append(services),
    )
    monkeypatch.setattr(
        disk_space_guard,
        "send_disk_alert_email_best_effort",
        lambda level, free, guard: alerts.append(level),
    )
    held = disk_space_guard.enforce_disk_space_guard(
        disk_guard_config(tmp_path), ["compose"], 1000.0, False
    )
    assert held == ["qbittorrent"]
    assert stopped == [["qbittorrent"]]
    assert alerts == ["critical"]
    assert (
        json.loads((tmp_path / "alert-state.json").read_text())["level"] == "critical"
    )


def test_enforce_ok_holds_nothing_and_stays_silent(tmp_path, monkeypatch):
    alerts = []
    monkeypatch.setattr(
        disk_space_guard, "free_gigabytes_available", lambda path: 100.0
    )

    def must_not_stop(base, services, dry_run):
        raise AssertionError("disk guard must not stop anything when free space is ok")

    monkeypatch.setattr(disk_space_guard, "stop_on_demand_services", must_not_stop)
    monkeypatch.setattr(
        disk_space_guard,
        "send_disk_alert_email_best_effort",
        lambda level, free, guard: alerts.append(level),
    )
    held = disk_space_guard.enforce_disk_space_guard(
        disk_guard_config(tmp_path), ["compose"], 1000.0, False
    )
    assert held == []
    assert alerts == []


def test_enforce_warning_holds_nothing_alerts_once_and_persists(tmp_path, monkeypatch):
    alerts = []
    monkeypatch.setattr(disk_space_guard, "free_gigabytes_available", lambda path: 20.0)

    def must_not_stop(base, services, dry_run):
        raise AssertionError("disk guard must not stop anything at the warning level")

    monkeypatch.setattr(disk_space_guard, "stop_on_demand_services", must_not_stop)
    monkeypatch.setattr(
        disk_space_guard,
        "send_disk_alert_email_best_effort",
        lambda level, free, guard: alerts.append(level) or True,
    )
    held = disk_space_guard.enforce_disk_space_guard(
        disk_guard_config(tmp_path), ["compose"], 1000.0, False
    )
    assert held == []
    assert alerts == ["warning"]
    assert json.loads((tmp_path / "alert-state.json").read_text())["level"] == "warning"


def test_dry_run_does_not_email_or_persist_alert_state(tmp_path, monkeypatch):
    sends = []
    monkeypatch.setattr(disk_space_guard, "free_gigabytes_available", lambda path: 5.0)
    monkeypatch.setattr(
        disk_space_guard,
        "stop_on_demand_services",
        lambda base, services, dry_run: None,
    )
    monkeypatch.setattr(
        disk_space_guard,
        "send_disk_alert_email_best_effort",
        lambda level, free, guard: sends.append(level) or True,
    )
    held = disk_space_guard.enforce_disk_space_guard(
        disk_guard_config(tmp_path), ["compose"], 1000.0, True
    )
    assert held == ["qbittorrent"]
    assert sends == []
    assert not (tmp_path / "alert-state.json").exists()


def test_critical_disk_holds_fill_service_out_of_keep_chain_always_on(
    tmp_path, monkeypatch
):
    started = []
    monkeypatch.setattr(disk_space_guard, "free_gigabytes_available", lambda path: 5.0)
    monkeypatch.setattr(
        disk_space_guard,
        "stop_on_demand_services",
        lambda base, services, dry_run: None,
    )
    monkeypatch.setattr(
        disk_space_guard,
        "send_disk_alert_email_best_effort",
        lambda level, free, guard: None,
    )
    monkeypatch.setattr(
        supervisor_core, "running_on_demand_services", lambda base, services: set()
    )
    monkeypatch.setattr(
        supervisor_core,
        "maybe_run_missing_search_sweep",
        lambda configuration, now, dry_run: None,
    )
    monkeypatch.setattr(
        supervisor_core,
        "start_on_demand_services",
        lambda base, services, dry_run: started.append(list(services)),
    )
    monkeypatch.setattr(
        supervisor_core, "write_last_active_epoch", lambda path, now: None
    )
    configuration = {
        "base_command": ["compose"],
        "on_demand_services": ON_DEMAND_SERVICES,
        "state_file_path": "/state",
        "jellyseerr_url": "http://jellyseerr",
        "jellyseerr_api_key": "key",
        "radarr_url": "http://radarr",
        "sonarr_url": "http://sonarr",
        "radarr_config_file": "/radarr.xml",
        "sonarr_config_file": "/sonarr.xml",
        "recent_pending_window_seconds": 21600,
        "idle_grace_seconds": 1200,
        "keep_chain_always_on": True,
        "disk_guard": disk_guard_config(tmp_path),
    }
    supervisor_core.run_supervisor_tick(configuration, 1000.0, False)
    assert started, "expected keep-chain-always-on to start the chain"
    assert "qbittorrent" not in started[0]
    assert "radarr" in started[0]
