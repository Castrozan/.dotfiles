import json
from pathlib import Path
import stat
import sys
import tomllib

import pytest

import seed_interactive_profiles
from seed_interactive_profiles import main, seed_profile


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


@pytest.fixture
def profile_activation(tmp_path, monkeypatch):
    directory = tmp_path / ".codex"
    store = tmp_path / "store"
    store.mkdir()
    source = store / "profile.toml"
    source.write_text('developer_instructions = "managed"\n')
    manifest = store / "sources.json"
    manifest.write_text(json.dumps({"dotfiles-interactive": str(source)}))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(seed_interactive_profiles, "NIX_STORE", store)
    monkeypatch.setattr(sys, "argv", ["seed", str(directory), str(manifest)])
    return directory, manifest, source


def test_activation_reads_store_sources_into_the_managed_directory(profile_activation):
    directory, _, source = profile_activation

    main()

    assert (
        directory / "dotfiles-interactive.config.toml"
    ).read_bytes() == source.read_bytes()


def test_activation_rejects_an_unmanaged_destination(
    profile_activation, tmp_path, monkeypatch
):
    _, manifest, _ = profile_activation
    monkeypatch.setattr(sys, "argv", ["seed", str(tmp_path), str(manifest)])

    with pytest.raises(ValueError, match="managed Codex directory"):
        main()


@pytest.mark.parametrize("source_kind", ["manifest", "source", "symlink"])
def test_activation_rejects_sources_outside_the_store(
    profile_activation, tmp_path, monkeypatch, source_kind
):
    directory, manifest, source = profile_activation
    outside = tmp_path / "outside"
    outside.write_text(source.read_text())
    if source_kind == "manifest":
        outside.write_text(manifest.read_text())
        monkeypatch.setattr(sys, "argv", ["seed", str(directory), str(outside)])
    else:
        if source_kind == "symlink":
            source.unlink()
            source.symlink_to(outside)
        else:
            manifest.write_text(json.dumps({"dotfiles-interactive": str(outside)}))

    with pytest.raises(ValueError, match="Nix store"):
        main()

    assert not directory.exists()


def test_activation_rejects_profile_name_traversal(profile_activation):
    directory, manifest, source = profile_activation
    manifest.write_text(json.dumps({"../escaped": str(source)}))

    with pytest.raises(ValueError, match="profile name"):
        main()

    assert not directory.exists()
