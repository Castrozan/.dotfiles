import stat
import tomllib

import pytest

from seed_interactive_profiles import seed_profile


def test_profile_migration_replaces_the_symlink_without_changing_its_source(tmp_path):
    source = tmp_path / "profile.config.toml.nix-source"
    source.write_text('developer_instructions = "instructions"\n')
    source.chmod(0o444)
    profile = tmp_path / "profile.config.toml"
    profile.symlink_to(source)

    seed_profile(source, profile)

    assert not profile.is_symlink()
    assert profile.read_bytes() == source.read_bytes()
    assert stat.S_IMODE(profile.stat().st_mode) == 0o600
    assert stat.S_IMODE(source.stat().st_mode) == 0o444


def test_rebuild_preserves_model_selection_and_refreshes_managed_instructions(tmp_path):
    source = tmp_path / "profile.config.toml.nix-source"
    source.write_text('developer_instructions = "current"\n')
    profile = tmp_path / "profile.config.toml"
    seed_profile(source, profile)
    profile.write_text(
        'developer_instructions = "old"\nmodel = "selected"\n'
        'model_reasoning_effort = "high"\nremoved_setting = true\n'
    )

    seed_profile(source, profile)
    first_modified = profile.stat().st_mtime_ns
    seed_profile(source, profile)

    assert tomllib.loads(profile.read_text()) == {
        "developer_instructions": "current",
        "model": "selected",
        "model_reasoning_effort": "high",
    }
    assert profile.stat().st_mtime_ns == first_modified


def test_explicit_workspace_model_settings_remain_authoritative(tmp_path):
    source = tmp_path / "profile.config.toml.nix-source"
    source.write_text('model = "declared"\nmodel_reasoning_effort = "xhigh"\n')
    profile = tmp_path / "profile.config.toml"
    profile.write_text('model = "selected"\nmodel_reasoning_effort = "low"\n')

    seed_profile(source, profile)

    assert profile.read_bytes() == source.read_bytes()


def test_invalid_profile_is_preserved_and_fails_activation(tmp_path):
    source = tmp_path / "profile.config.toml.nix-source"
    source.write_text('developer_instructions = "current"\n')
    profile = tmp_path / "profile.config.toml"
    profile.write_text('model = "unfinished')

    with pytest.raises(tomllib.TOMLDecodeError):
        seed_profile(source, profile)

    assert profile.read_text() == 'model = "unfinished'
