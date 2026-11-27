import plistlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


INSTALLED_APPLICATION_PATH = Path("/Applications/Rex.app")
DISK_IMAGE_APPLICATION_NAME = "Rex.app"
INSTALL_COMMAND_TIMEOUT_SECONDS = 600


def installed_rex_build():
    information_path = INSTALLED_APPLICATION_PATH / "Contents" / "Info.plist"
    if not information_path.exists():
        return None
    with information_path.open("rb") as information_file:
        build = plistlib.load(information_file)["CFBundleVersion"]
    if not build.isdigit():
        raise ValueError(f"Invalid Rex build: {build!r}")
    return int(build)


def installed_build_meets_minimum(minimum_build):
    installed_build = installed_rex_build()
    return installed_build is not None and installed_build >= minimum_build


def validated_disk_image(disk_image):
    disk_image_path = Path(disk_image)
    if (
        disk_image_path.is_absolute()
        and disk_image_path.suffix == ".dmg"
        and disk_image_path.is_file()
    ):
        return disk_image_path
    raise ValueError(f"Invalid Rex disk image: {disk_image!r}")


def ensure_rex_application(minimum_build, disk_image, owner):
    if installed_build_meets_minimum(minimum_build):
        return
    disk_image_path = validated_disk_image(disk_image)
    print(
        f"Installing Rex build >= {minimum_build} from the vendor disk image",
        flush=True,
    )
    staged_application = INSTALLED_APPLICATION_PATH.with_name("Rex.app.installing")
    shutil.rmtree(staged_application, ignore_errors=True)
    copy_application_from_disk_image(disk_image_path, staged_application)
    subprocess.run(
        ["/usr/sbin/chown", "-R", owner, str(staged_application)],
        check=True,
        timeout=INSTALL_COMMAND_TIMEOUT_SECONDS,
    )
    shutil.rmtree(INSTALLED_APPLICATION_PATH, ignore_errors=True)
    staged_application.rename(INSTALLED_APPLICATION_PATH)
    if not installed_build_meets_minimum(minimum_build):
        raise RuntimeError(
            f"Rex build >= {minimum_build} is required; installed: {installed_rex_build()}"
        )


def copy_application_from_disk_image(disk_image_path, destination):
    with tempfile.TemporaryDirectory() as mount_point:
        subprocess.run(
            [
                "/usr/bin/hdiutil",
                "attach",
                "-nobrowse",
                "-readonly",
                "-mountpoint",
                mount_point,
                str(disk_image_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            timeout=INSTALL_COMMAND_TIMEOUT_SECONDS,
        )
        try:
            subprocess.run(
                [
                    "/usr/bin/ditto",
                    str(Path(mount_point) / DISK_IMAGE_APPLICATION_NAME),
                    str(destination),
                ],
                check=True,
                timeout=INSTALL_COMMAND_TIMEOUT_SECONDS,
            )
        finally:
            subprocess.run(
                ["/usr/bin/hdiutil", "detach", mount_point],
                check=True,
                stdout=subprocess.DEVNULL,
                timeout=INSTALL_COMMAND_TIMEOUT_SECONDS,
            )


if __name__ == "__main__":
    ensure_rex_application(int(sys.argv[1]), sys.argv[2], sys.argv[3])
