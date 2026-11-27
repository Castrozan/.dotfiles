import importlib.util
import plistlib
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def application_installer(tmp_path, monkeypatch):
    source = Path(__file__).parents[2] / "scripts" / "ensure_rex_application.py"
    specification = importlib.util.spec_from_file_location(
        "ensure_rex_application", source
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    monkeypatch.setattr(module, "INSTALLED_APPLICATION_PATH", tmp_path / "Rex.app")
    monkeypatch.setattr(module.subprocess, "run", Mock())
    return module


@pytest.fixture
def disk_image(tmp_path):
    image = tmp_path / "Rex-0.1.0-2181.dmg"
    image.write_bytes(b"image")
    return image


def write_application_build(application_path, build):
    contents = application_path / "Contents"
    contents.mkdir(parents=True, exist_ok=True)
    with (contents / "Info.plist").open("wb") as information_file:
        plistlib.dump({"CFBundleVersion": build}, information_file)


def copy_application_writing_build(application_installer, build):
    def copy(disk_image_path, destination):
        write_application_build(destination, build)

    application_installer.copy_application_from_disk_image = Mock(side_effect=copy)


def test_missing_application_is_installed_from_disk_image(
    application_installer, disk_image
):
    copy_application_writing_build(application_installer, "2181")
    application_installer.ensure_rex_application(2181, str(disk_image), "someone")
    application_installer.copy_application_from_disk_image.assert_called_once()
    application_installer.subprocess.run.assert_called_once_with(
        [
            "/usr/sbin/chown",
            "-R",
            "someone",
            str(
                application_installer.INSTALLED_APPLICATION_PATH.with_name(
                    "Rex.app.installing"
                )
            ),
        ],
        check=True,
    )
    assert application_installer.installed_rex_build() == 2181


def test_application_updated_past_the_pin_is_left_alone(
    application_installer, disk_image
):
    write_application_build(application_installer.INSTALLED_APPLICATION_PATH, "2200")
    copy_application_writing_build(application_installer, "2181")
    application_installer.ensure_rex_application(2181, str(disk_image), "someone")
    application_installer.copy_application_from_disk_image.assert_not_called()
    assert application_installer.installed_rex_build() == 2200


def test_older_application_is_replaced(application_installer, disk_image):
    write_application_build(application_installer.INSTALLED_APPLICATION_PATH, "2100")
    copy_application_writing_build(application_installer, "2181")
    application_installer.ensure_rex_application(2181, str(disk_image), "someone")
    assert application_installer.installed_rex_build() == 2181


def test_disk_image_older_than_the_pin_stops_activation(
    application_installer, disk_image
):
    copy_application_writing_build(application_installer, "2100")
    with pytest.raises(RuntimeError, match="installed: 2100"):
        application_installer.ensure_rex_application(2181, str(disk_image), "someone")


def test_relative_disk_image_stops_before_copying(application_installer):
    copy_application_writing_build(application_installer, "2181")
    with pytest.raises(ValueError, match="Invalid Rex disk image"):
        application_installer.ensure_rex_application(2181, "Rex.dmg", "someone")
    application_installer.copy_application_from_disk_image.assert_not_called()


def test_malformed_installed_build_stops_before_copying(
    application_installer, disk_image
):
    write_application_build(application_installer.INSTALLED_APPLICATION_PATH, "0.1.0")
    copy_application_writing_build(application_installer, "2181")
    with pytest.raises(ValueError, match="Invalid Rex build"):
        application_installer.ensure_rex_application(2181, str(disk_image), "someone")
    application_installer.copy_application_from_disk_image.assert_not_called()
