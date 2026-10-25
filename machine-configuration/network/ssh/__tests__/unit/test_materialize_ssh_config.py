import os
import stat

import pytest

import materialize_ssh_config as materializer


@pytest.fixture
def configuration_paths(tmp_path):
    directory = tmp_path / ".ssh"
    directory.mkdir(mode=0o700)
    source = tmp_path / "generated-config"
    source.write_text(
        "Include ~/.ssh/config.d/*\nHost rin kira\n  StrictHostKeyChecking yes\n"
    )
    source.chmod(0o444)
    return source, directory / "config"


def test_materializes_exact_generated_config_with_secure_user_ownership(
    configuration_paths,
):
    source, destination = configuration_paths

    materializer.materialize_ssh_config(source, destination)

    assert destination.read_bytes() == source.read_bytes()
    assert destination.stat().st_uid == os.geteuid()
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert not destination.is_symlink()
    assert stat.S_IMODE(source.stat().st_mode) == 0o444


def test_refreshes_existing_file_from_current_declarative_source(configuration_paths):
    source, destination = configuration_paths
    materializer.materialize_ssh_config(source, destination)
    source.chmod(0o600)
    source.write_text("Host rin\n  HostName current.example\n")
    source.chmod(0o444)

    materializer.materialize_ssh_config(source, destination)

    assert destination.read_bytes() == source.read_bytes()
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600


def test_refuses_destination_symlink_without_touching_its_target(
    configuration_paths, tmp_path
):
    source, destination = configuration_paths
    other = tmp_path / "unrelated-config"
    other.write_text("preserve me")
    destination.symlink_to(other)

    with pytest.raises(ValueError, match="user-owned regular file"):
        materializer.materialize_ssh_config(source, destination)

    assert destination.is_symlink()
    assert other.read_text() == "preserve me"


def test_refuses_group_writable_parent(configuration_paths):
    source, destination = configuration_paths
    destination.parent.chmod(0o770)

    with pytest.raises(ValueError, match="not writable by other users"):
        materializer.materialize_ssh_config(source, destination)

    assert not destination.exists()


def test_preserves_concurrent_edit_and_cleans_temporary_file(
    configuration_paths, monkeypatch
):
    source, destination = configuration_paths
    destination.write_text("previous config")
    original_fsync = materializer.os.fsync

    def edit_during_activation(descriptor):
        original_fsync(descriptor)
        destination.write_text("concurrent edit")

    monkeypatch.setattr(materializer.os, "fsync", edit_during_activation)

    with pytest.raises(RuntimeError, match="preserving the concurrent edit"):
        materializer.materialize_ssh_config(source, destination)

    assert destination.read_text() == "concurrent edit"
    assert list(destination.parent.glob(".config-*")) == []


def test_failed_replace_preserves_existing_config_and_cleans_temporary_file(
    configuration_paths, monkeypatch
):
    source, destination = configuration_paths
    destination.write_text("previous config")

    def fail_replace(source_path, destination_path):
        raise OSError("replacement failed")

    monkeypatch.setattr(materializer.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replacement failed"):
        materializer.materialize_ssh_config(source, destination)

    assert destination.read_text() == "previous config"
    assert list(destination.parent.glob(".config-*")) == []
