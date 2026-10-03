import plistlib
import re
import subprocess
from pathlib import Path


KARABINER_APPLICATION_INFORMATION_PATH = Path(
    "/Applications/Karabiner-Elements.app/Contents/Info.plist"
)


def version_components(version):
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"Invalid Karabiner version: {version!r}")
    return tuple(int(component) for component in version.split("."))


def installed_karabiner_version():
    if not KARABINER_APPLICATION_INFORMATION_PATH.exists():
        return None
    with KARABINER_APPLICATION_INFORMATION_PATH.open("rb") as information_file:
        return plistlib.load(information_file)["CFBundleShortVersionString"]


def ensure_karabiner_version(minimum_version, installer_package):
    minimum_components = version_components(minimum_version)
    installed_version = installed_karabiner_version()
    if installed_version_meets_minimum(installed_version, minimum_components):
        return
    install_karabiner_package(minimum_version, minimum_components, installer_package)


def installed_version_meets_minimum(installed_version, minimum_components):
    return (
        installed_version
        and version_components(installed_version) >= minimum_components
    )


def install_karabiner_package(minimum_version, minimum_components, installer_package):
    package_path = Path(installer_package)
    if (
        not package_path.is_absolute()
        or package_path.suffix != ".pkg"
        or not package_path.is_file()
    ):
        raise ValueError(f"Invalid Karabiner installer package: {installer_package!r}")
    print(
        f"Installing Karabiner >= {minimum_version} from the vendor package", flush=True
    )
    subprocess.run(
        [
            "/usr/sbin/installer",
            "-pkg",
            str(package_path),
            "-target",
            "/",
        ],
        check=True,
    )
    installed_version = installed_karabiner_version()
    if not installed_version_meets_minimum(installed_version, minimum_components):
        raise RuntimeError(
            f"Karabiner >= {minimum_version} is required; installed: {installed_version}"
        )


if __name__ == "__main__":
    ensure_karabiner_version(
        "@MINIMUM_KARABINER_VERSION@",
        "@KARABINER_INSTALLER_PACKAGE@",
    )
