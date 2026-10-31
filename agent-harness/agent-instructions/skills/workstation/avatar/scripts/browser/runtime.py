import os
import signal
import shlex
import socket
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
        if not endpoint.exists():
            raise RuntimeError(
                "The owned avatar browser has no endpoint; stop it before restarting"
            )
        print(int(endpoint.read_text().splitlines()[0]))
        return
    remove_stale_locks(profile)
    endpoint.unlink(missing_ok=True)
    with (profile / "browser.log").open("w") as output:
        process = subprocess.Popen(
            [
                "chromium",
                f"--user-data-dir={profile}",
                "--remote-debugging-port=0",
                "--autoplay-policy=no-user-gesture-required",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
                "--ozone-platform=x11",
                f"--app={url}",
            ],
            stdout=output,
            stderr=output,
            start_new_session=True,
        )
    (profile / "browser.pid").write_text(str(process.pid))
    wait_for_endpoint(profile, process)


def wait_for_endpoint(profile, process):
    endpoint = profile / "DevToolsActivePort"
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError("The avatar browser did not start a new owned instance")
        if endpoint.exists():
            (profile / "browser.pid").write_text(
                str(owned_process(profile) or process.pid)
            )
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
        for _ in range(50):
            if owned_process(profile) != identifier:
                break
            time.sleep(0.1)
        else:
            raise TimeoutError("The owned avatar browser did not stop")
    path.unlink(missing_ok=True)
    remove_stale_locks(profile)


def locked_process_identifier(profile):
    lock = profile / "SingletonLock"
    if not lock.is_symlink():
        return
    target = str(lock.readlink()).rsplit("-", 1)
    if len(target) == 2 and target[0] == socket.gethostname() and target[1].isdigit():
        return int(target[1])


def candidate_identifiers(profile):
    identifiers = [locked_process_identifier(profile)]
    path = profile / "browser.pid"
    if path.exists():
        identifiers.append(int(path.read_text()))
    return identifiers


def process_arguments(identifier):
    arguments = (
        (Path("/proc") / str(identifier) / "cmdline").read_bytes().split(bytes([0]))
    )
    if len(arguments) == 2 and arguments[-1] == b"":
        return [part.encode() for part in shlex.split(arguments[0].decode())]
    return arguments


def owned_process(profile):
    for identifier in candidate_identifiers(profile):
        if identifier is None:
            continue
        try:
            if f"--user-data-dir={profile}".encode() in process_arguments(identifier):
                return identifier
        except (ProcessLookupError, FileNotFoundError):
            pass


def controls():
    profile = profile_directory()
    if owned_process(profile) is None:
        raise RuntimeError("Start the avatar before opening its controls")
    subprocess.Popen(
        [
            "chromium",
            f"--user-data-dir={profile}",
            "--app=http://localhost:3000/controls.html",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def remove_stale_locks(profile):
    identifier = locked_process_identifier(profile)
    if identifier is None:
        return
    try:
        if (Path("/proc") / str(identifier) / "cmdline").read_bytes():
            return
    except FileNotFoundError:
        pass
    for name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        (profile / name).unlink(missing_ok=True)


if __name__ == "__main__":
    if sys.argv[1] == "start":
        start(sys.argv[2])
    elif sys.argv[1] == "stop":
        stop()
    elif sys.argv[1] == "controls":
        controls()
    else:
        raise ValueError("Use start URL or stop")
