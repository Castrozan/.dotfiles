import sys
from pathlib import Path

SUPERVISOR_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "on_demand_supervisor"
)
sys.path.insert(0, str(SUPERVISOR_PACKAGE_DIRECTORY_PATH))

import supervisor_core

CONFIGURATION = {
    "radarr_url": "http://radarr",
    "sonarr_url": "http://sonarr",
    "radarr_config_file": "/radarr.xml",
    "sonarr_config_file": "/sonarr.xml",
    "missing_search_state_file": "/missing-sweep-epoch",
    "missing_search_interval_seconds": 21600,
}


def patch_common(monkeypatch, last_sweep_epoch, sweep_return):
    sweep_calls = []
    stamped_epochs = []
    monkeypatch.setattr(
        supervisor_core, "read_arr_api_key_from_config_xml", lambda path: "key"
    )
    monkeypatch.setattr(
        supervisor_core, "read_last_active_epoch", lambda path: last_sweep_epoch
    )
    monkeypatch.setattr(
        supervisor_core,
        "write_last_active_epoch",
        lambda path, now: stamped_epochs.append(now),
    )
    monkeypatch.setattr(
        supervisor_core,
        "run_missing_search_sweep",
        lambda *args, **kwargs: sweep_calls.append(True) or sweep_return,
    )
    return sweep_calls, stamped_epochs


def test_sweep_is_skipped_within_the_throttle_interval(monkeypatch):
    sweep_calls, stamped_epochs = patch_common(monkeypatch, 1000.0, True)
    supervisor_core.maybe_run_missing_search_sweep(CONFIGURATION, 1100.0, False)
    assert sweep_calls == []
    assert stamped_epochs == []


def test_sweep_runs_and_stamps_when_interval_elapsed_and_indexers_active(monkeypatch):
    sweep_calls, stamped_epochs = patch_common(monkeypatch, 1000.0, True)
    supervisor_core.maybe_run_missing_search_sweep(CONFIGURATION, 1000.0 + 30000, False)
    assert sweep_calls == [True]
    assert stamped_epochs == [1000.0 + 30000]


def test_sweep_runs_without_stamping_when_all_indexers_deferred(monkeypatch):
    sweep_calls, stamped_epochs = patch_common(monkeypatch, None, False)
    supervisor_core.maybe_run_missing_search_sweep(CONFIGURATION, 5000.0, False)
    assert sweep_calls == [True]
    assert stamped_epochs == []


def test_on_demand_idle_tick_sweeps_before_the_idle_stop_decision(monkeypatch):
    call_order = []
    monkeypatch.setattr(
        supervisor_core, "enforce_data_mount_guard", lambda *args, **kwargs: False
    )
    monkeypatch.setattr(
        supervisor_core, "actionable_requests", lambda *args, **kwargs: ([], [])
    )
    monkeypatch.setattr(
        supervisor_core, "running_on_demand_services", lambda base, services: {"radarr"}
    )
    monkeypatch.setattr(
        supervisor_core, "read_arr_api_key_from_config_xml", lambda path: "key"
    )
    monkeypatch.setattr(
        supervisor_core,
        "maybe_run_missing_search_sweep",
        lambda configuration, now, dry_run: call_order.append(("sweep", now)),
    )
    monkeypatch.setattr(
        supervisor_core,
        "stop_chain_when_idle_past_grace",
        lambda *args, **kwargs: call_order.append(("stop", None)),
    )
    configuration = {
        "base_command": ["compose"],
        "on_demand_services": ["radarr", "sonarr"],
        "state_file_path": "/state",
        "jellyseerr_url": "http://jellyseerr",
        "jellyseerr_api_key": "key",
        "radarr_url": "http://radarr",
        "sonarr_url": "http://sonarr",
        "radarr_config_file": "/radarr.xml",
        "sonarr_config_file": "/sonarr.xml",
        "recent_pending_window_seconds": 21600,
        "idle_grace_seconds": 1200,
        "keep_chain_always_on": False,
        "disk_guard": None,
    }
    supervisor_core.run_supervisor_tick(configuration, 1000.0, False)
    assert call_order == [("sweep", 1000.0), ("stop", None)]
