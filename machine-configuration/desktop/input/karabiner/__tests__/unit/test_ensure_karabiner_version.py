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


@pytest.fixture
def installer_package(tmp_path):
    package = tmp_path / "Karabiner-Elements.pkg"
    package.write_bytes(b"package")
    return package


@pytest.mark.parametrize("installed_version", ["16.3.0", "16.10.0", "17.0.0"])
def test_fixed_versions_do_not_launch_installer(version_installer, installed_version):
    write_installed_version(version_installer, installed_version)
    version_installer.ensure_karabiner_version("16.3.0", "/unused.pkg")
    version_installer.subprocess.run.assert_not_called()


def test_minor_version_upgrade_targets_only_karabiner(
    version_installer, installer_package
):
    write_installed_version(version_installer, "16.0.0")
    version_installer.subprocess.run.side_effect = (
        lambda *arguments, **keywords: write_installed_version(
            version_installer, "16.3.0"
        )
    )
    version_installer.ensure_karabiner_version("16.3.0", installer_package)
    version_installer.subprocess.run.assert_called_once_with(
        [
            "/usr/sbin/installer",
            "-pkg",
            str(installer_package),
            "-target",
            "/",
        ],
        check=True,
    )
    version_installer.subprocess.run.reset_mock()
    version_installer.ensure_karabiner_version("16.3.0", installer_package)
    version_installer.subprocess.run.assert_not_called()


def test_activation_keeps_installer_privileges(version_installer, installer_package):
    write_installed_version(version_installer, "16.0.0")

    def install_with_activation_privileges(command, **keywords):
        assert command[0] == "/usr/sbin/installer"
        write_installed_version(version_installer, "16.3.0")

    version_installer.subprocess.run.side_effect = install_with_activation_privileges
    version_installer.ensure_karabiner_version("16.3.0", installer_package)


def test_missing_application_is_installed(version_installer, installer_package):
    version_installer.subprocess.run.side_effect = (
        lambda *arguments, **keywords: write_installed_version(
            version_installer, "16.3.0"
        )
    )
    version_installer.ensure_karabiner_version("16.3.0", installer_package)
    command = version_installer.subprocess.run.call_args.args[0]
    assert command == [
        "/usr/sbin/installer",
        "-pkg",
        str(installer_package),
        "-target",
        "/",
    ]


def test_unsuccessful_upgrade_stops_activation(version_installer, installer_package):
    write_installed_version(version_installer, "16.0.0")
    with pytest.raises(RuntimeError, match="installed: 16.0.0"):
        version_installer.ensure_karabiner_version("16.3.0", installer_package)


def test_installer_failure_stops_activation(version_installer, installer_package):
    write_installed_version(version_installer, "16.0.0")
    version_installer.subprocess.run.side_effect = subprocess.CalledProcessError(
        1, ["/usr/sbin/installer"]
    )
    with pytest.raises(subprocess.CalledProcessError):
        version_installer.ensure_karabiner_version("16.3.0", installer_package)


def test_malformed_version_stops_before_installing(version_installer):
    write_installed_version(version_installer, "invalid")
    with pytest.raises(ValueError, match="Invalid Karabiner version"):
        version_installer.ensure_karabiner_version("16.3.0", "/unused.pkg")
    version_installer.subprocess.run.assert_not_called()


@pytest.mark.parametrize(
    "installer_package", ["--help", "relative.pkg", "/missing.pkg"]
)
def test_invalid_package_stops_before_installing(version_installer, installer_package):
    write_installed_version(version_installer, "16.0.0")
    with pytest.raises(ValueError, match="Invalid Karabiner installer package"):
        version_installer.ensure_karabiner_version("16.3.0", installer_package)
    version_installer.subprocess.run.assert_not_called()


def test_directory_is_not_an_installer_package(version_installer, tmp_path):
    package = tmp_path / "directory.pkg"
    package.mkdir()
    write_installed_version(version_installer, "16.0.0")
    with pytest.raises(ValueError, match="Invalid Karabiner installer package"):
        version_installer.ensure_karabiner_version("16.3.0", package)
    version_installer.subprocess.run.assert_not_called()
