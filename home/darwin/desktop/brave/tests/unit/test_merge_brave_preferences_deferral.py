import json


def _write_json(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as json_file:
        json.dump(content, json_file)


def test_merge_defers_without_writing_preferences_when_brave_is_running(
    merge_brave_preferences_module, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        merge_brave_preferences_module, "brave_is_currently_running", lambda: True
    )
    overrides_path = tmp_path / "overrides.json"
    _write_json(overrides_path, {"brave": {"pinned": True}})
    brave_user_data_directory = tmp_path / "Brave-Browser"
    default_profile_preferences_path = (
        brave_user_data_directory / "Default" / "Preferences"
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "merge-brave-preferences",
            str(overrides_path),
            str(brave_user_data_directory),
        ],
    )

    exit_code = merge_brave_preferences_module.main()

    assert (
        exit_code
        == merge_brave_preferences_module.PREFERENCE_MERGE_DEFERRED_BECAUSE_BRAVE_RUNNING_EXIT_CODE
    )
    assert not default_profile_preferences_path.exists()


def test_merge_applies_and_returns_zero_when_brave_is_not_running(
    merge_brave_preferences_module, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        merge_brave_preferences_module, "brave_is_currently_running", lambda: False
    )
    overrides_path = tmp_path / "overrides.json"
    _write_json(overrides_path, {"brave": {"pinned": True}})
    brave_user_data_directory = tmp_path / "Brave-Browser"
    default_profile_preferences_path = (
        brave_user_data_directory / "Default" / "Preferences"
    )
    _write_json(default_profile_preferences_path, {"existing": {"kept": 1}})
    monkeypatch.setattr(
        "sys.argv",
        [
            "merge-brave-preferences",
            str(overrides_path),
            str(brave_user_data_directory),
        ],
    )

    exit_code = merge_brave_preferences_module.main()

    assert exit_code == 0
    with default_profile_preferences_path.open() as merged_preferences_file:
        merged = json.load(merged_preferences_file)
    assert merged["existing"] == {"kept": 1}
    assert merged["brave"] == {"pinned": True}
