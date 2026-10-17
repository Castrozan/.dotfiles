import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def profile_directory():
    return (
        Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        / "avatar/browser"
    )


def start(url):
    profile = profile_directory()
    profile.mkdir(parents=True, exist_ok=True, mode=0o700)
    endpoint = profile / "DevToolsActivePort"
    if owned_process(profile) is not None:
        print(int(endpoint.read_text().splitlines()[0]))
        return
    endpoint.unlink(missing_ok=True)
    with (profile / "browser.log").open("w") as output:
        process = subprocess.Popen(
            [
                "chromium",
                f"--user-data-dir={profile}",
                "--remote-debugging-port=0",
                "--autoplay-policy=no-user-gesture-required",
                f"--app={url}",
            ],
            stdout=output,
            stderr=output,
            start_new_session=True,
        )
    (profile / "browser.pid").write_text(str(process.pid))
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError("The avatar browser did not start a new owned instance")
        if endpoint.exists():
            print(int(endpoint.read_text().splitlines()[0]))
            return
        time.sleep(0.1)
    process.terminate()
    raise TimeoutError("The avatar browser did not expose its own endpoint")


def stop():
    profile = profile_directory()
    path = profile / "browser.pid"
    identifier = owned_process(profile)
    if identifier is not None:
        os.kill(identifier, signal.SIGTERM)
    path.unlink(missing_ok=True)


def owned_process(profile):
    path = profile / "browser.pid"
    if not path.exists():
        return
    identifier = int(path.read_text())
    try:
        arguments = (
            (Path("/proc") / str(identifier) / "cmdline").read_bytes().split(bytes([0]))
        )
        if f"--user-data-dir={profile}".encode() in arguments:
            return identifier
    except (ProcessLookupError, FileNotFoundError):
        pass


if __name__ == "__main__":
    if sys.argv[1] == "start":
        start(sys.argv[2])
    elif sys.argv[1] == "stop":
        stop()
    else:
        raise ValueError("Use start URL or stop")
