import sys
from pathlib import Path

SUPERVISOR_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "on_demand_supervisor"
)
sys.path.insert(0, str(SUPERVISOR_PACKAGE_DIRECTORY_PATH))

import supervisor_core


def patch_decision_dependencies(monkeypatch, queue_active, last_active_epoch):
    written_epochs = []
    stopped_service_sets = []
    monkeypatch.setattr(
        supervisor_core, "arr_download_queue_active", lambda endpoints: queue_active
    )
    monkeypatch.setattr(
        supervisor_core, "read_last_active_epoch", lambda path: last_active_epoch
    )
    monkeypatch.setattr(
        supervisor_core,
        "write_last_active_epoch",
        lambda path, now: written_epochs.append(now),
    )
    monkeypatch.setattr(
        supervisor_core,
        "stop_on_demand_services",
        lambda base_command, services, dry_run: stopped_service_sets.append(services),
    )
    return written_epochs, stopped_service_sets


def test_active_queue_refreshes_baseline_and_never_stops(monkeypatch):
    written_epochs, stopped_service_sets = patch_decision_dependencies(
        monkeypatch, queue_active=True, last_active_epoch=0.0
    )
    supervisor_core.stop_chain_when_idle_past_grace(
        ["compose"], ["radarr"], "/state", 1000.0, 1200, [], False
    )
    assert written_epochs == [1000.0]
    assert stopped_service_sets == []


def test_missing_baseline_records_now_and_keeps_chain_up(monkeypatch):
    written_epochs, stopped_service_sets = patch_decision_dependencies(
        monkeypatch, queue_active=False, last_active_epoch=None
    )
    supervisor_core.stop_chain_when_idle_past_grace(
        ["compose"], ["radarr"], "/state", 2000.0, 1200, [], False
    )
    assert written_epochs == [2000.0]
    assert stopped_service_sets == []


def test_stops_chain_once_idle_reaches_grace(monkeypatch):
    written_epochs, stopped_service_sets = patch_decision_dependencies(
        monkeypatch, queue_active=False, last_active_epoch=0.0
    )
    supervisor_core.stop_chain_when_idle_past_grace(
        ["compose"], ["radarr", "sonarr"], "/state", 1200.0, 1200, [], False
    )
    assert stopped_service_sets == [["radarr", "sonarr"]]


def test_keeps_chain_up_while_idle_stays_below_grace(monkeypatch):
    written_epochs, stopped_service_sets = patch_decision_dependencies(
        monkeypatch, queue_active=False, last_active_epoch=100.0
    )
    supervisor_core.stop_chain_when_idle_past_grace(
        ["compose"], ["radarr"], "/state", 1200.0, 1200, [], False
    )
    assert stopped_service_sets == []
