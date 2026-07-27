import json


def test_settings_are_a_real_file_merging_the_overlay_onto_the_shared_settings(
    run_seed,
):
    invoke, isolated = run_seed
    assert invoke().returncode == 0
    isolated_settings = isolated / "settings.json"
    assert not isolated_settings.is_symlink()
    settings = json.loads(isolated_settings.read_text())
    assert settings["model"] == "sonnet", "the overlay must win on a key collision"
    assert settings["theme"] == "dark", "shared keys the overlay omits must survive"
    assert settings["enabledPlugins"] == {"work": True}


def test_settings_are_owner_readable_only(run_seed):
    invoke, isolated = run_seed
    assert invoke().returncode == 0
    assert (isolated / "settings.json").stat().st_mode & 0o777 == 0o600


def test_a_second_run_keeps_runtime_keys_written_into_the_isolated_settings(run_seed):
    invoke, isolated = run_seed
    assert invoke().returncode == 0
    isolated_settings = isolated / "settings.json"
    settings = json.loads(isolated_settings.read_text())
    settings["voiceEnabled"] = True
    isolated_settings.write_text(json.dumps(settings))

    assert invoke().returncode == 0
    reseeded = json.loads(isolated_settings.read_text())
    assert reseeded["voiceEnabled"] is True, "reseeding must not clobber runtime keys"
    assert reseeded["model"] == "sonnet", "reseeding must reapply the declared overlay"


def test_a_second_run_adopts_shared_settings_changed_since_the_first_seed(
    run_seed, shared_config_directory
):
    invoke, isolated = run_seed
    assert invoke().returncode == 0
    assert json.loads((isolated / "settings.json").read_text())["effortLevel"] == "high"

    shared_settings_path = shared_config_directory / "settings.json"
    shared_settings = json.loads(shared_settings_path.read_text())
    shared_settings["effortLevel"] = "xhigh"
    shared_settings["model"] = "claude-opus-5[1m]"
    shared_settings_path.write_text(json.dumps(shared_settings))

    assert invoke().returncode == 0
    reseeded = json.loads((isolated / "settings.json").read_text())
    assert reseeded["effortLevel"] == "xhigh", (
        "a shared setting changed after the first seed must reach the isolated config"
    )
    assert reseeded["model"] == "sonnet", (
        "the overlay must still win on a key collision"
    )


def test_a_second_run_drops_a_setting_the_shared_config_stopped_declaring(
    run_seed, shared_config_directory
):
    invoke, isolated = run_seed
    assert invoke().returncode == 0

    shared_settings_path = shared_config_directory / "settings.json"
    shared_settings = json.loads(shared_settings_path.read_text())
    del shared_settings["retiredSetting"]
    shared_settings_path.write_text(json.dumps(shared_settings))

    assert invoke().returncode == 0
    reseeded = json.loads((isolated / "settings.json").read_text())
    assert "retiredSetting" not in reseeded, (
        "a setting retired from the shared config must not linger in the isolated config"
    )
