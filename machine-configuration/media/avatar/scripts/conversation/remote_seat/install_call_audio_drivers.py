import pathlib
import shutil
import subprocess
import sys

DRIVER_DIRECTORY = pathlib.Path("/Library/Audio/Plug-Ins/HAL")
COMMAND_TIMEOUT_SECONDS = 60


def is_installed(packaged_driver, installed_driver):
    if not installed_driver.exists():
        return False
    comparison = subprocess.run(
        ["/usr/bin/diff", "-rq", str(packaged_driver), str(installed_driver)],
        capture_output=True,
        check=False,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )
    return comparison.returncode == 0


def install(packaged_driver, installed_driver):
    shutil.rmtree(installed_driver, ignore_errors=True)
    installed_driver.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(packaged_driver, installed_driver, symlinks=True)


def restart_audio_server():
    subprocess.run(
        ["/usr/bin/killall", "coreaudiod"], check=True, timeout=COMMAND_TIMEOUT_SECONDS
    )


def install_missing(packaged_drivers):
    missing = [
        (packaged_driver, DRIVER_DIRECTORY / packaged_driver.name)
        for packaged_driver in packaged_drivers
        if not is_installed(packaged_driver, DRIVER_DIRECTORY / packaged_driver.name)
    ]
    for packaged_driver, installed_driver in missing:
        install(packaged_driver, installed_driver)
    return [installed_driver.name for _, installed_driver in missing]


def main():
    installed = install_missing([pathlib.Path(argument) for argument in sys.argv[1:]])
    if installed:
        restart_audio_server()
        print(f"Installed the call audio drivers {', '.join(installed)}")


if __name__ == "__main__":
    main()
