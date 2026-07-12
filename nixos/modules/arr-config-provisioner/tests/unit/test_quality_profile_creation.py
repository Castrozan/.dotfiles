from quality_profile_test_doubles import (
    quality_profile_provisioner,
    stub_api,
    stub_create,
)


def test_creates_absent_profile_cloned_from_template(monkeypatch):
    updated = stub_api(
        monkeypatch,
        [
            {"id": 1, "name": "Portuguese (BR) Dublado"},
            {"id": 2, "name": "English"},
        ],
        [
            {
                "id": 6,
                "name": "HD - 720p/1080p",
                "upgradeAllowed": True,
                "minFormatScore": 0,
                "cutoffFormatScore": 0,
                "items": [{"quality": {"id": 9}, "allowed": True}],
                "formatItems": [{"format": 99, "name": "Stale", "score": 99}],
            }
        ],
    )
    created = stub_create(monkeypatch)
    outcomes = quality_profile_provisioner.provision_quality_profiles(
        "b",
        "k",
        [
            {
                "name": "PT-BR Dublado",
                "cloneFrom": "HD - 720p/1080p",
                "minFormatScore": 1,
                "formatScores": {"Portuguese (BR) Dublado": 50},
            }
        ],
        False,
    )
    assert outcomes == ["created"]
    assert updated == []
    resource, body = created[0]
    assert resource == "qualityprofile"
    assert "id" not in body
    assert body["name"] == "PT-BR Dublado"
    assert body["minFormatScore"] == 1
    assert body["items"] == [{"quality": {"id": 9}, "allowed": True}]
    assert {
        "format": 1,
        "name": "Portuguese (BR) Dublado",
        "score": 50,
    } in body["formatItems"]
    assert {"format": 2, "name": "English", "score": 0} in body["formatItems"]
    assert {"format": 99, "name": "Stale", "score": 99} not in body["formatItems"]


def test_dry_run_create_writes_nothing(monkeypatch):
    stub_api(
        monkeypatch,
        [{"id": 1, "name": "Portuguese (BR) Dublado"}],
        [{"id": 6, "name": "HD - 720p/1080p", "items": [], "formatItems": []}],
    )
    created = stub_create(monkeypatch)
    outcomes = quality_profile_provisioner.provision_quality_profiles(
        "b",
        "k",
        [
            {
                "name": "PT-BR Dublado",
                "cloneFrom": "HD - 720p/1080p",
                "formatScores": {},
            }
        ],
        True,
    )
    assert outcomes == ["would-create"]
    assert created == []


def test_absent_template_reports_missing_without_create(monkeypatch):
    stub_api(monkeypatch, [{"id": 1, "name": "Portuguese (BR) Dublado"}], [])
    created = stub_create(monkeypatch)
    outcomes = quality_profile_provisioner.provision_quality_profiles(
        "b",
        "k",
        [
            {
                "name": "PT-BR Dublado",
                "cloneFrom": "HD - 720p/1080p",
                "formatScores": {},
            }
        ],
        False,
    )
    assert outcomes == ["missing-profile"]
    assert created == []
