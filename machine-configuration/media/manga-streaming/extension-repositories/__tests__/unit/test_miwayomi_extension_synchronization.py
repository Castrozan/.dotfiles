import importlib
import sys
from pathlib import Path

import pytest

PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "suwayomi_extension_repositories"
)
sys.path.insert(0, str(PACKAGE_DIRECTORY_PATH))

miwayomi_extension_synchronization = importlib.import_module(
    "miwayomi_extension_synchronization"
)


class MiwayomiClient:
    def __init__(self):
        self.installed = {
            "current.package": "2.0",
            "removed.package": "4.0",
        }
        self.calls = []

    def read_installed_extensions(self, _base_url):
        return [
            {"pkg": package, "version": version}
            for package, version in self.installed.items()
        ]

    def uninstall_extension(self, _base_url, package_name):
        self.calls.append(("uninstall", package_name))
        self.installed.pop(package_name, None)


def test_removes_declared_broken_extensions_and_verifies_the_result():
    client = MiwayomiClient()
    policy = miwayomi_extension_synchronization.ExtensionPolicy(
        removed_packages=("removed.package", "not.installed.package"),
    )

    result = miwayomi_extension_synchronization.synchronize_extensions(
        "http://miwayomi:4567",
        policy,
        client,
    )

    assert result == {"removed_packages": ["removed.package"]}
    assert client.calls == [("uninstall", "removed.package")]
    assert client.installed == {"current.package": "2.0"}


def test_is_idempotent_after_declared_extensions_are_absent():
    client = MiwayomiClient()
    client.installed.pop("removed.package")

    result = miwayomi_extension_synchronization.synchronize_extensions(
        "http://miwayomi:4567",
        miwayomi_extension_synchronization.ExtensionPolicy(
            removed_packages=("removed.package",),
        ),
        client,
    )

    assert result == {"removed_packages": []}
    assert client.calls == []


def test_refuses_when_an_uninstalled_extension_remains_reported():
    client = MiwayomiClient()
    client.uninstall_extension = lambda _base_url, package_name: client.calls.append(
        ("uninstall", package_name)
    )

    with pytest.raises(ValueError, match="removed.package"):
        miwayomi_extension_synchronization.synchronize_extensions(
            "http://miwayomi:4567",
            miwayomi_extension_synchronization.ExtensionPolicy(
                removed_packages=("removed.package",),
            ),
            client,
        )
