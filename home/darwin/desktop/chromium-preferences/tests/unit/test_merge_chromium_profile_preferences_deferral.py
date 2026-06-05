import json


def _write_json(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as json_file:
        json.dump(content, json_file)


def test_merge_defers_without_writing_preferences_when_browser_is_running(
    merge_chromium_profile_preferences_module, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        merge_chromium_profile_preferences_module,
        "chromium_browser_process_is_running",
        lambda browser_process_name: True,
    )
    overrides_path = tmp_path / "overrides.json"
    _write_json(overrides_path, {"browser": {"pinned": True}})
    browser_user_data_directory = tmp_path / "Chrome"
    default_profile_preferences_path = (
        browser_user_data_directory / "Default" / "Preferences"
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "merge-chromium-profile-preferences",
            str(overrides_path),
            str(browser_user_data_directory),
            "Google Chrome",
        ],
    )

    exit_code = merge_chromium_profile_preferences_module.main()

    assert (
        exit_code
        == merge_chromium_profile_preferences_module.PREFERENCE_MERGE_DEFERRED_BECAUSE_BROWSER_RUNNING_EXIT_CODE
    )
    assert not default_profile_preferences_path.exists()


def test_merge_applies_and_returns_zero_when_browser_is_not_running(
    merge_chromium_profile_preferences_module, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        merge_chromium_profile_preferences_module,
        "chromium_browser_process_is_running",
        lambda browser_process_name: False,
    )
    overrides_path = tmp_path / "overrides.json"
    _write_json(overrides_path, {"browser": {"pinned": True}})
    browser_user_data_directory = tmp_path / "Chrome"
    default_profile_preferences_path = (
        browser_user_data_directory / "Default" / "Preferences"
    )
    _write_json(default_profile_preferences_path, {"existing": {"kept": 1}})
    monkeypatch.setattr(
        "sys.argv",
        [
            "merge-chromium-profile-preferences",
            str(overrides_path),
            str(browser_user_data_directory),
            "Google Chrome",
        ],
    )

    exit_code = merge_chromium_profile_preferences_module.main()

    assert exit_code == 0
    with default_profile_preferences_path.open() as merged_preferences_file:
        merged = json.load(merged_preferences_file)
    assert merged["existing"] == {"kept": 1}
    assert merged["browser"] == {"pinned": True}
