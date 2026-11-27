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


STOPS_ACTIVATION = None


@pytest.mark.parametrize(
    ("installed_build", "disk_image_build", "resulting_build"),
    [
        (None, "2181", 2181),
        ("2100", "2181", 2181),
        ("2181", "2100", 2181),
        (None, "2100", STOPS_ACTIVATION),
    ],
)
def test_activation_leaves_rex_at_or_past_the_pinned_build(
    application_installer,
    disk_image,
    installed_build,
    disk_image_build,
    resulting_build,
):
    if installed_build is not None:
        write_application_build(
            application_installer.INSTALLED_APPLICATION_PATH, installed_build
        )
    copy_application_writing_build(application_installer, disk_image_build)
    if resulting_build is STOPS_ACTIVATION:
        with pytest.raises(RuntimeError, match=f"installed: {disk_image_build}"):
            application_installer.ensure_rex_application(
                2181, str(disk_image), "someone"
            )
        return
    application_installer.ensure_rex_application(2181, str(disk_image), "someone")
    assert application_installer.installed_rex_build() == resulting_build
