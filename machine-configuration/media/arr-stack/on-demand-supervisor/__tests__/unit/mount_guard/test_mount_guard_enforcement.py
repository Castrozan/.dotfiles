import json

import mount_health_guard
import supervisor_core
from mount_guard_fixtures import ON_DEMAND_SERVICES, base_configuration


def test_guard_disabled_never_intervenes(tmp_path, monkeypatch):
    monkeypatch.setattr(mount_health_guard, "data_mount_is_healthy", lambda path: False)

    def must_not_stop(base, services, dry_run):
        raise AssertionError("disabled mount guard must never stop the stack")

    monkeypatch.setattr(mount_health_guard, "stop_on_demand_services", must_not_stop)
    aborted = mount_health_guard.enforce_data_mount_guard(
        base_configuration(tmp_path, mount_guard_enabled=False),
        ["compose"],
        1000.0,
        False,
    )
    assert aborted is False


def test_healthy_mount_returns_false_and_does_not_stop(tmp_path, monkeypatch):
    monkeypatch.setattr(mount_health_guard, "data_mount_is_healthy", lambda path: True)

    def must_not_stop(base, services, dry_run):
        raise AssertionError("healthy mount must not stop the stack")

    monkeypatch.setattr(mount_health_guard, "stop_on_demand_services", must_not_stop)
    aborted = mount_health_guard.enforce_data_mount_guard(
        base_configuration(tmp_path), ["compose"], 1000.0, False
    )
    assert aborted is False


def test_lost_mount_stops_stack_alerts_once_and_persists(tmp_path, monkeypatch):
    stopped = []
    alerts = []
    monkeypatch.setattr(mount_health_guard, "data_mount_is_healthy", lambda path: False)
    monkeypatch.setattr(
        mount_health_guard,
        "stop_on_demand_services",
        lambda base, services, dry_run: stopped.append(list(services)),
    )
    monkeypatch.setattr(
        mount_health_guard,
        "send_mount_alert_email_best_effort",
        lambda guard: alerts.append("lost") or True,
    )
    aborted = mount_health_guard.enforce_data_mount_guard(
        base_configuration(tmp_path), ["compose"], 1000.0, False
    )
    assert aborted is True
    assert stopped == [ON_DEMAND_SERVICES]
    assert alerts == ["lost"]
    assert (
        json.loads((tmp_path / "mount-alert-state.json").read_text())["level"] == "lost"
    )


def test_lost_mount_does_not_re_alert_within_reminder_window(tmp_path, monkeypatch):
    (tmp_path / "mount-alert-state.json").write_text(
        json.dumps({"level": "lost", "last_alert_epoch": 1000.0})
    )
    alerts = []
    monkeypatch.setattr(mount_health_guard, "data_mount_is_healthy", lambda path: False)
    monkeypatch.setattr(
        mount_health_guard,
        "stop_on_demand_services",
        lambda base, services, dry_run: None,
    )
    monkeypatch.setattr(
        mount_health_guard,
        "send_mount_alert_email_best_effort",
        lambda guard: alerts.append("lost") or True,
    )
    mount_health_guard.enforce_data_mount_guard(
        base_configuration(tmp_path), ["compose"], 1100.0, False
    )
    assert alerts == []


def test_lost_mount_re_alerts_after_reminder_window(tmp_path, monkeypatch):
    (tmp_path / "mount-alert-state.json").write_text(
        json.dumps({"level": "lost", "last_alert_epoch": 1000.0})
    )
    alerts = []
    monkeypatch.setattr(mount_health_guard, "data_mount_is_healthy", lambda path: False)
    monkeypatch.setattr(
        mount_health_guard,
        "stop_on_demand_services",
        lambda base, services, dry_run: None,
    )
    monkeypatch.setattr(
        mount_health_guard,
        "send_mount_alert_email_best_effort",
        lambda guard: alerts.append("lost") or True,
    )
    now_epoch = 1000.0 + 21600
    mount_health_guard.enforce_data_mount_guard(
        base_configuration(tmp_path), ["compose"], now_epoch, False
    )
    assert alerts == ["lost"]
    assert (
        json.loads((tmp_path / "mount-alert-state.json").read_text())[
            "last_alert_epoch"
        ]
        == now_epoch
    )


def test_failed_email_persists_zero_epoch_to_force_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(mount_health_guard, "data_mount_is_healthy", lambda path: False)
    monkeypatch.setattr(
        mount_health_guard,
        "stop_on_demand_services",
        lambda base, services, dry_run: None,
    )
    monkeypatch.setattr(
        mount_health_guard,
        "send_mount_alert_email_best_effort",
        lambda guard: False,
    )
    mount_health_guard.enforce_data_mount_guard(
        base_configuration(tmp_path), ["compose"], 1000.0, False
    )
    persisted = json.loads((tmp_path / "mount-alert-state.json").read_text())
    assert persisted["level"] == "lost"
    assert persisted["last_alert_epoch"] == 0.0


def test_recovery_clears_lost_state(tmp_path, monkeypatch):
    (tmp_path / "mount-alert-state.json").write_text(
        json.dumps({"level": "lost", "last_alert_epoch": 1000.0})
    )
    monkeypatch.setattr(mount_health_guard, "data_mount_is_healthy", lambda path: True)
    aborted = mount_health_guard.enforce_data_mount_guard(
        base_configuration(tmp_path), ["compose"], 2000.0, False
    )
    assert aborted is False
    assert (
        json.loads((tmp_path / "mount-alert-state.json").read_text())["level"] == "ok"
    )


def test_dry_run_lost_mount_does_not_email_or_persist(tmp_path, monkeypatch):
    sends = []
    monkeypatch.setattr(mount_health_guard, "data_mount_is_healthy", lambda path: False)
    monkeypatch.setattr(
        mount_health_guard,
        "stop_on_demand_services",
        lambda base, services, dry_run: None,
    )
    monkeypatch.setattr(
        mount_health_guard,
        "send_mount_alert_email_best_effort",
        lambda guard: sends.append("lost") or True,
    )
    mount_health_guard.enforce_data_mount_guard(
        base_configuration(tmp_path), ["compose"], 1000.0, True
    )
    assert sends == []
    assert not (tmp_path / "mount-alert-state.json").exists()


def test_tick_aborts_early_when_mount_unhealthy(tmp_path, monkeypatch):
    monkeypatch.setattr(
        supervisor_core, "enforce_data_mount_guard", lambda config, base, now, dry: True
    )

    def must_not_run_disk_guard(config, base, now, dry):
        raise AssertionError(
            "tick must abort before the disk-space guard on lost mount"
        )

    monkeypatch.setattr(
        supervisor_core, "held_down_services_from_disk_guard", must_not_run_disk_guard
    )
    configuration = base_configuration(tmp_path)
    configuration["keep_chain_always_on"] = True
    supervisor_core.run_supervisor_tick(configuration, 1000.0, False)
