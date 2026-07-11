import sys
from pathlib import Path

PROVISIONER_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_config_provisioner"
)
sys.path.insert(0, str(PROVISIONER_PACKAGE_DIRECTORY_PATH))

import quality_profile_provisioner


def stub_api(monkeypatch, custom_formats, profiles):
    updated = []
    resources = {"customformat": custom_formats, "qualityprofile": profiles}
    monkeypatch.setattr(
        quality_profile_provisioner,
        "get_resource_list",
        lambda base, key, resource: resources[resource],
    )
    monkeypatch.setattr(
        quality_profile_provisioner,
        "update_resource",
        lambda base, key, resource, resource_id, body: updated.append(
            (resource_id, body)
        ),
    )
    return updated


def test_build_format_items_scores_known_and_defaults_zero():
    items = quality_profile_provisioner.build_format_items(
        [{"id": 1, "name": "Multi-Subtitle"}, {"id": 2, "name": "Other"}],
        {"Multi-Subtitle": 25},
    )
    assert items == [
        {"format": 1, "name": "Multi-Subtitle", "score": 25},
        {"format": 2, "name": "Other", "score": 0},
    ]


def test_scores_existing_profile_and_overrides_fields(monkeypatch):
    updated = stub_api(
        monkeypatch,
        [{"id": 1, "name": "Multi-Subtitle"}, {"id": 2, "name": "VOSTFR / French"}],
        [
            {
                "id": 6,
                "name": "HD - 720p/1080p",
                "upgradeAllowed": False,
                "minFormatScore": 0,
                "cutoffFormatScore": 0,
                "formatItems": [],
            }
        ],
    )
    outcomes = quality_profile_provisioner.provision_quality_profiles(
        "b",
        "k",
        [
            {
                "name": "HD - 720p/1080p",
                "upgradeAllowed": True,
                "minFormatScore": -100,
                "cutoffFormatScore": 25,
                "formatScores": {"Multi-Subtitle": 25, "VOSTFR / French": -25},
            }
        ],
        False,
    )
    assert outcomes == ["updated"]
    resource_id, body = updated[0]
    assert resource_id == 6
    assert body["upgradeAllowed"] is True
    assert body["minFormatScore"] == -100
    assert body["cutoffFormatScore"] == 25
    assert body["formatItems"] == [
        {"format": 1, "name": "Multi-Subtitle", "score": 25},
        {"format": 2, "name": "VOSTFR / French", "score": -25},
    ]


def test_preserves_fields_absent_from_desired(monkeypatch):
    updated = stub_api(
        monkeypatch,
        [{"id": 1, "name": "Multi-Subtitle"}],
        [
            {
                "id": 6,
                "name": "HD - 720p/1080p",
                "upgradeAllowed": False,
                "minFormatScore": 7,
                "cutoffFormatScore": 3,
                "formatItems": [],
            }
        ],
    )
    quality_profile_provisioner.provision_quality_profiles(
        "b",
        "k",
        [{"name": "HD - 720p/1080p", "upgradeAllowed": True}],
        False,
    )
    _, body = updated[0]
    assert body["upgradeAllowed"] is True
    assert body["minFormatScore"] == 7
    assert body["cutoffFormatScore"] == 3


def test_reports_missing_profile_without_writing(monkeypatch):
    updated = stub_api(monkeypatch, [{"id": 1, "name": "Multi-Subtitle"}], [])
    outcomes = quality_profile_provisioner.provision_quality_profiles(
        "b", "k", [{"name": "Absent Profile", "formatScores": {}}], False
    )
    assert outcomes == ["missing-profile"]
    assert updated == []


def test_dry_run_writes_nothing(monkeypatch):
    updated = stub_api(
        monkeypatch,
        [{"id": 1, "name": "Multi-Subtitle"}],
        [{"id": 6, "name": "HD - 720p/1080p", "formatItems": []}],
    )
    outcomes = quality_profile_provisioner.provision_quality_profiles(
        "b",
        "k",
        [{"name": "HD - 720p/1080p", "formatScores": {"Multi-Subtitle": 25}}],
        True,
    )
    assert outcomes == ["would-update"]
    assert updated == []


def test_unknown_format_still_updates(monkeypatch):
    updated = stub_api(
        monkeypatch,
        [{"id": 1, "name": "Multi-Subtitle"}],
        [{"id": 6, "name": "HD - 720p/1080p", "formatItems": []}],
    )
    outcomes = quality_profile_provisioner.provision_quality_profiles(
        "b",
        "k",
        [{"name": "HD - 720p/1080p", "formatScores": {"Nonexistent": 10}}],
        False,
    )
    assert outcomes == ["updated"]
    _, body = updated[0]
    assert body["formatItems"] == [{"format": 1, "name": "Multi-Subtitle", "score": 0}]
