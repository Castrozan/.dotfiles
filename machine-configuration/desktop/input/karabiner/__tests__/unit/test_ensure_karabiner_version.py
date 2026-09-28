import importlib.util
import plistlib
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def version_installer(tmp_path, monkeypatch):
    source = Path(__file__).parents[2] / "scripts" / "ensure_karabiner_version.py"
    specification = importlib.util.spec_from_file_location(
        "ensure_karabiner_version", source
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    monkeypatch.setattr(
        module, "KARABINER_APPLICATION_INFORMATION_PATH", tmp_path / "Info.plist"
    )
    monkeypatch.setattr(module.subprocess, "run", Mock())
    return module


def write_installed_version(version_installer, version):
    with version_installer.KARABINER_APPLICATION_INFORMATION_PATH.open(
        "wb"
    ) as information_file:
        plistlib.dump({"CFBundleShortVersionString": version}, information_file)


@pytest.mark.parametrize("installed_version", ["16.3.0", "16.10.0", "17.0.0"])
def test_fixed_versions_do_not_launch_homebrew(version_installer, installed_version):
    write_installed_version(version_installer, installed_version)
    version_installer.ensure_karabiner_version("16.3.0", "/brew", "alice")
    version_installer.subprocess.run.assert_not_called()


def test_minor_version_upgrade_targets_only_karabiner(version_installer):
    write_installed_version(version_installer, "16.0.0")
    version_installer.subprocess.run.side_effect = (
        lambda *arguments, **keywords: write_installed_version(
            version_installer, "16.3.0"
        )
    )
    version_installer.ensure_karabiner_version("16.3.0", "/brew", "alice")
    version_installer.subprocess.run.assert_called_once_with(
        [
            "/usr/bin/sudo",
            "--user",
            "alice",
            "--set-home",
            "/brew",
            "upgrade",
            "--cask",
            "--greedy",
            "karabiner-elements",
        ],
        check=True,
    )
    version_installer.subprocess.run.reset_mock()
    version_installer.ensure_karabiner_version("16.3.0", "/brew", "alice")
    version_installer.subprocess.run.assert_not_called()


def test_missing_application_is_installed(version_installer):
    version_installer.subprocess.run.side_effect = (
        lambda *arguments, **keywords: write_installed_version(
            version_installer, "16.3.0"
        )
    )
    version_installer.ensure_karabiner_version("16.3.0", "/brew", "alice")
    command = version_installer.subprocess.run.call_args.args[0]
    assert command[-3:] == ["install", "--cask", "karabiner-elements"]


def test_unsuccessful_upgrade_stops_activation(version_installer):
    write_installed_version(version_installer, "16.0.0")
    with pytest.raises(RuntimeError, match="installed: 16.0.0"):
        version_installer.ensure_karabiner_version("16.3.0", "/brew", "alice")


def test_installer_failure_stops_activation(version_installer):
    write_installed_version(version_installer, "16.0.0")
    version_installer.subprocess.run.side_effect = subprocess.CalledProcessError(
        1, ["/brew"]
    )
    with pytest.raises(subprocess.CalledProcessError):
        version_installer.ensure_karabiner_version("16.3.0", "/brew", "alice")


def test_malformed_version_stops_before_installing(version_installer):
    write_installed_version(version_installer, "invalid")
    with pytest.raises(ValueError, match="Invalid Karabiner version"):
        version_installer.ensure_karabiner_version("16.3.0", "/brew", "alice")
    version_installer.subprocess.run.assert_not_called()
