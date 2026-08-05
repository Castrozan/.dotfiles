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


def test_merge_targets_local_state_and_preserves_unrelated_keys_when_target_is_overridden(
    merge_chromium_profile_preferences_module, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        merge_chromium_profile_preferences_module,
        "chromium_browser_process_is_running",
        lambda browser_process_name: False,
    )
    overrides_path = tmp_path / "overrides.json"
    _write_json(
        overrides_path,
        {"profile": {"info_cache": {"Profile 2": {"avatar_icon": "distinctive"}}}},
    )
    browser_user_data_directory = tmp_path / "chrome-global"
    local_state_path = browser_user_data_directory / "Local State"
    default_profile_preferences_path = (
        browser_user_data_directory / "Default" / "Preferences"
    )
    _write_json(
        local_state_path,
        {
            "browser": {"last_version": "137"},
            "profile": {"info_cache": {"Profile 1": {"avatar_icon": "work"}}},
        },
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "merge-chromium-profile-preferences",
            str(overrides_path),
            str(browser_user_data_directory),
            "Google Chrome",
            "Local State",
        ],
    )

    exit_code = merge_chromium_profile_preferences_module.main()

    assert exit_code == 0
    assert not default_profile_preferences_path.exists()
    with local_state_path.open() as merged_local_state_file:
        merged = json.load(merged_local_state_file)
    assert merged["browser"] == {"last_version": "137"}
    assert merged["profile"]["info_cache"]["Profile 1"] == {"avatar_icon": "work"}
    assert merged["profile"]["info_cache"]["Profile 2"] == {
        "avatar_icon": "distinctive"
    }


def test_merge_refuses_to_overwrite_an_existing_but_unreadable_target(
    merge_chromium_profile_preferences_module, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        merge_chromium_profile_preferences_module,
        "chromium_browser_process_is_running",
        lambda browser_process_name: False,
    )
    overrides_path = tmp_path / "overrides.json"
    _write_json(overrides_path, {"profile": {"pinned": True}})
    browser_user_data_directory = tmp_path / "chrome-global"
    local_state_path = browser_user_data_directory / "Local State"
    local_state_path.parent.mkdir(parents=True, exist_ok=True)
    corrupt_local_state_bytes = '{"profile": {"info_cache": '
    local_state_path.write_text(corrupt_local_state_bytes)
    monkeypatch.setattr(
        "sys.argv",
        [
            "merge-chromium-profile-preferences",
            str(overrides_path),
            str(browser_user_data_directory),
            "Google Chrome",
            "Local State",
        ],
    )

    exit_code = merge_chromium_profile_preferences_module.main()

    assert exit_code != 0
    assert (
        exit_code
        != merge_chromium_profile_preferences_module.PREFERENCE_MERGE_DEFERRED_BECAUSE_BROWSER_RUNNING_EXIT_CODE
    )
    assert local_state_path.read_text() == corrupt_local_state_bytes
