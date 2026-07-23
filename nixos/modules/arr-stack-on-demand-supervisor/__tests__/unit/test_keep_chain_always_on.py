import sys
from pathlib import Path

SUPERVISOR_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "on_demand_supervisor"
)
sys.path.insert(0, str(SUPERVISOR_PACKAGE_DIRECTORY_PATH))

import supervisor_core

ON_DEMAND_SERVICES = ["radarr", "sonarr", "prowlarr", "qbittorrent", "bazarr"]


def configuration_with_always_on(keep_chain_always_on):
    return {
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
        "keep_chain_always_on": keep_chain_always_on,
    }


def test_always_on_starts_full_chain_and_never_queries_jellyseerr(monkeypatch):
    started_service_sets = []
    written_epochs = []
    jellyseerr_calls = []
    sweep_calls = []
    monkeypatch.setattr(
        supervisor_core, "running_on_demand_services", lambda base, services: set()
    )
    monkeypatch.setattr(
        supervisor_core,
        "maybe_run_missing_search_sweep",
        lambda configuration, now, dry_run: sweep_calls.append(now),
    )
    monkeypatch.setattr(
        supervisor_core,
        "start_on_demand_services",
        lambda base, services, dry_run: started_service_sets.append(services),
    )
    monkeypatch.setattr(
        supervisor_core,
        "write_last_active_epoch",
        lambda path, now: written_epochs.append(now),
    )
    monkeypatch.setattr(
        supervisor_core,
        "actionable_requests",
        lambda *args, **kwargs: jellyseerr_calls.append(True) or ([], []),
    )
    supervisor_core.run_supervisor_tick(
        configuration_with_always_on(True), 1000.0, False
    )
    assert started_service_sets == [ON_DEMAND_SERVICES]
    assert written_epochs == [1000.0]
    assert jellyseerr_calls == []
    assert sweep_calls == [1000.0]


def test_always_on_holds_without_restart_when_full_chain_is_up(monkeypatch):
    started_service_sets = []
    monkeypatch.setattr(
        supervisor_core,
        "running_on_demand_services",
        lambda base, services: set(services),
    )
    monkeypatch.setattr(
        supervisor_core,
        "maybe_run_missing_search_sweep",
        lambda configuration, now, dry_run: None,
    )
    monkeypatch.setattr(
        supervisor_core,
        "start_on_demand_services",
        lambda base, services, dry_run: started_service_sets.append(services),
    )
    monkeypatch.setattr(
        supervisor_core, "write_last_active_epoch", lambda path, now: None
    )
    monkeypatch.setattr(
        supervisor_core, "actionable_requests", lambda *args, **kwargs: ([], [])
    )
    supervisor_core.run_supervisor_tick(
        configuration_with_always_on(True), 1000.0, False
    )
    assert started_service_sets == []
