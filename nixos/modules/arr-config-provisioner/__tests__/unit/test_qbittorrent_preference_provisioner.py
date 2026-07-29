import sys
from pathlib import Path

import pytest

PROVISIONER_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_config_provisioner"
)
sys.path.insert(0, str(PROVISIONER_PACKAGE_DIRECTORY_PATH))

import qbittorrent_preference_provisioner

DECLARED_PREFERENCES = {
    "max_active_torrents": -1,
    "max_active_uploads": -1,
    "max_ratio_enabled": False,
}


def stub_qbittorrent(monkeypatch, live_preferences):
    written = []
    monkeypatch.setattr(
        qbittorrent_preference_provisioner,
        "build_authenticated_opener",
        lambda base_url, username, password: "opener",
    )
    monkeypatch.setattr(
        qbittorrent_preference_provisioner,
        "read_preferences",
        lambda opener, base_url: live_preferences,
    )
    monkeypatch.setattr(
        qbittorrent_preference_provisioner,
        "write_preferences",
        lambda opener, base_url, preferences: written.append(preferences),
    )
    return written


def test_only_the_differing_preferences_are_written(monkeypatch):
    written = stub_qbittorrent(
        monkeypatch,
        {
            "max_active_torrents": 5,
            "max_active_uploads": -1,
            "max_ratio_enabled": False,
        },
    )

    qbittorrent_preference_provisioner.provision_qbittorrent_preferences(
        "http://arr:8080", "admin", "secret", DECLARED_PREFERENCES, False
    )

    assert written == [{"max_active_torrents": -1}]


def test_a_matching_qbittorrent_is_left_alone(monkeypatch):
    written = stub_qbittorrent(monkeypatch, dict(DECLARED_PREFERENCES))

    outcome = qbittorrent_preference_provisioner.provision_qbittorrent_preferences(
        "http://arr:8080", "admin", "secret", DECLARED_PREFERENCES, False
    )

    assert written == []
    assert outcome == "already matching"


def test_a_dry_run_writes_nothing(monkeypatch):
    written = stub_qbittorrent(monkeypatch, {"max_active_torrents": 5})

    outcome = qbittorrent_preference_provisioner.provision_qbittorrent_preferences(
        "http://arr:8080", "admin", "secret", DECLARED_PREFERENCES, True
    )

    assert written == []
    assert outcome.startswith("would set")


def test_a_missing_password_skips_instead_of_authenticating(monkeypatch):
    written = stub_qbittorrent(monkeypatch, {})

    outcome = qbittorrent_preference_provisioner.provision_qbittorrent_preferences(
        "http://arr:8080", "admin", "", DECLARED_PREFERENCES, False
    )

    assert written == []
    assert "no web ui password" in outcome


def test_an_absent_declaration_skips_instead_of_clearing_preferences(monkeypatch):
    written = stub_qbittorrent(monkeypatch, {"max_active_torrents": 5})

    outcome = qbittorrent_preference_provisioner.provision_qbittorrent_preferences(
        "http://arr:8080", "admin", "secret", [], False
    )

    assert written == []
    assert "nothing declared" in outcome


@pytest.mark.parametrize(
    "stopping_preference",
    [
        "max_ratio_enabled",
        "max_seeding_time_enabled",
        "max_inactive_seeding_time_enabled",
    ],
)
def test_a_declaration_that_stops_seeding_is_refused(monkeypatch, stopping_preference):
    stub_qbittorrent(monkeypatch, {})

    with pytest.raises(ValueError, match="hit and run"):
        qbittorrent_preference_provisioner.provision_qbittorrent_preferences(
            "http://arr:8080",
            "admin",
            "secret",
            {**DECLARED_PREFERENCES, stopping_preference: True},
            False,
        )


@pytest.mark.parametrize(
    "capped_preference", ["max_active_torrents", "max_active_uploads"]
)
def test_a_finite_active_torrent_cap_is_refused(monkeypatch, capped_preference):
    stub_qbittorrent(monkeypatch, {})

    with pytest.raises(ValueError, match="finite active-torrent cap"):
        qbittorrent_preference_provisioner.provision_qbittorrent_preferences(
            "http://arr:8080",
            "admin",
            "secret",
            {**DECLARED_PREFERENCES, capped_preference: 5},
            False,
        )


def test_the_committed_declaration_passes_its_own_guard():
    import json

    declared = json.loads(
        (
            PROVISIONER_PACKAGE_DIRECTORY_PATH.parents[1]
            / "desired-state"
            / "qbittorrent"
            / "preferences.json"
        ).read_text()
    )
    qbittorrent_preference_provisioner.assert_desired_preferences_never_stop_seeding(
        declared
    )
