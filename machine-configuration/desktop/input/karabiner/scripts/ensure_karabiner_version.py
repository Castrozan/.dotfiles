import argparse
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


def ensure_karabiner_version(minimum_version, homebrew_binary, homebrew_user):
    minimum_components = version_components(minimum_version)
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", homebrew_user):
        raise ValueError(f"Invalid Homebrew user: {homebrew_user!r}")
    homebrew_path = Path(homebrew_binary)
    if not homebrew_path.is_absolute() or homebrew_path.name != "brew":
        raise ValueError(f"Invalid Homebrew executable: {homebrew_binary!r}")
    installed_version = installed_karabiner_version()
    if (
        installed_version
        and version_components(installed_version) >= minimum_components
    ):
        return
    operation = "upgrade" if installed_version else "install"
    print(f"Installing Karabiner >= {minimum_version} through Homebrew", flush=True)
    subprocess.run(
        [
            "/usr/bin/sudo",
            f"--user={homebrew_user}",
            "--set-home",
            "--",
            homebrew_binary,
            operation,
            "--cask",
            *(["--greedy"] if installed_version else []),
            "karabiner-elements",
        ],
        check=True,
    )
    installed_version = installed_karabiner_version()
    if (
        not installed_version
        or version_components(installed_version) < minimum_components
    ):
        raise RuntimeError(
            f"Karabiner >= {minimum_version} is required; installed: {installed_version}"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--minimum-version", required=True)
    parser.add_argument("--homebrew-binary", required=True)
    parser.add_argument("--homebrew-user", required=True)
    arguments = parser.parse_args()
    ensure_karabiner_version(
        arguments.minimum_version, arguments.homebrew_binary, arguments.homebrew_user
    )


if __name__ == "__main__":
    main()
