import sys
from pathlib import Path

PROVISIONER_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_config_provisioner"
)
sys.path.insert(0, str(PROVISIONER_PACKAGE_DIRECTORY_PATH))

import upsert_engine


def stub_api(monkeypatch, existing):
    created = []
    updated = []
    monkeypatch.setattr(
        upsert_engine, "get_resource_list", lambda base, key, resource: existing
    )
    monkeypatch.setattr(
        upsert_engine,
        "create_resource",
        lambda base, key, resource, body, force_save: created.append(
            (body, force_save)
        ),
    )
    monkeypatch.setattr(
        upsert_engine,
        "update_resource",
        lambda base, key, resource, resource_id, body, force_save: updated.append(
            (resource_id, body, force_save)
        ),
    )
    return created, updated


def test_creates_when_missing_passing_force_save(monkeypatch):
    created, updated = stub_api(monkeypatch, [])
    outcomes = upsert_engine.upsert_resource(
        "b", "k", "downloadclient", [{"name": "qBittorrent"}], "name", True, True, False
    )
    assert outcomes == ["created"]
    assert created == [({"name": "qBittorrent"}, True)]
    assert updated == []


def test_updates_when_present_and_update_supported(monkeypatch):
    created, updated = stub_api(monkeypatch, [{"id": 7, "name": "qBittorrent", "x": 0}])
    outcomes = upsert_engine.upsert_resource(
        "b",
        "k",
        "downloadclient",
        [{"name": "qBittorrent", "x": 1}],
        "name",
        True,
        True,
        False,
    )
    assert outcomes == ["updated"]
    assert updated == [(7, {"name": "qBittorrent", "x": 1, "id": 7}, True)]
    assert created == []


def test_leaves_present_rootfolder_alone_when_update_unsupported(monkeypatch):
    created, updated = stub_api(monkeypatch, [{"id": 1, "path": "/data/media/movies"}])
    outcomes = upsert_engine.upsert_resource(
        "b",
        "k",
        "rootfolder",
        [{"path": "/data/media/movies"}],
        "path",
        False,
        False,
        False,
    )
    assert outcomes == ["unchanged"]
    assert created == []
    assert updated == []


def test_creates_missing_rootfolder(monkeypatch):
    created, updated = stub_api(monkeypatch, [])
    outcomes = upsert_engine.upsert_resource(
        "b",
        "k",
        "rootfolder",
        [{"path": "/data/media/tv"}],
        "path",
        False,
        False,
        False,
    )
    assert outcomes == ["created"]
    assert created == [({"path": "/data/media/tv"}, False)]


def test_skips_object_with_unresolved_secret(monkeypatch):
    created, updated = stub_api(monkeypatch, [])
    obj = {
        "name": "qBittorrent",
        "fields": [{"name": "password", "value": "@QBITTORRENT_PASSWORD@"}],
    }
    outcomes = upsert_engine.upsert_resource(
        "b", "k", "downloadclient", [obj], "name", True, True, False
    )
    assert outcomes == ["skipped-missing-secret"]
    assert created == []
    assert updated == []


def test_dry_run_update_writes_nothing(monkeypatch):
    created, updated = stub_api(monkeypatch, [{"id": 3, "name": "qBittorrent"}])
    outcomes = upsert_engine.upsert_resource(
        "b",
        "k",
        "downloadclient",
        [{"name": "qBittorrent", "x": 1}],
        "name",
        True,
        True,
        True,
    )
    assert outcomes == ["would-update"]
    assert created == []
    assert updated == []


def test_dry_run_create_writes_nothing(monkeypatch):
    created, updated = stub_api(monkeypatch, [])
    outcomes = upsert_engine.upsert_resource(
        "b", "k", "downloadclient", [{"name": "qBittorrent"}], "name", True, True, True
    )
    assert outcomes == ["would-create"]
    assert created == []
    assert updated == []
