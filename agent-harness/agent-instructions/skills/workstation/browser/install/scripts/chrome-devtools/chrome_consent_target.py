import json
import os
import re
import secrets
import shlex
import subprocess
import time
from pathlib import Path


def run_tool(configuration, name, *arguments):
    return subprocess.run(
        [configuration[name], *arguments],
        check=True,
        capture_output=True,
        text=True,
        timeout=2,
    ).stdout


def chrome_identity(process_identifier, profile_directory, package_directory):
    directory = Path("/proc") / str(process_identifier)
    arguments = (
        directory.joinpath("cmdline").read_bytes().decode().strip("\0").split("\0")
    )
    if len(arguments) == 1:
        arguments = shlex.split(arguments[0])
    executable = directory.joinpath("exe").resolve(strict=True)
    if (
        directory.stat().st_uid != os.getuid()
        or not executable.is_relative_to(Path(package_directory))
        or executable.name != "chrome"
    ):
        raise RuntimeError("Target is not the native Chrome browser process")
    if f"--user-data-dir={profile_directory}" not in arguments:
        raise RuntimeError("Target does not own the managed Chrome Global profile")
    if any(
        argument.startswith(("--type=", "--app=", "--kiosk", "--headless"))
        for argument in arguments
    ):
        raise RuntimeError("Target is not a regular visible Chrome browser")
    return directory.joinpath("stat").read_text().rsplit(")", 1)[1].split()[19]


def current_target(configuration):
    clients = json.loads(run_tool(configuration, "hyprctl", "-j", "clients"))
    targets = [
        client
        for client in clients
        if client.get("class") == "chrome-global" and client.get("mapped")
    ]
    if len(targets) != 1:
        raise RuntimeError(
            "Expected exactly one managed Chrome window; refusing ambiguous targeting"
        )
    target = targets[0]
    if (
        target.get("fullscreen")
        or target.get("fullscreenClient")
        or target.get("hidden")
    ):
        raise RuntimeError("Chrome window must be visible and outside fullscreen")
    target["process_start"] = chrome_identity(
        target["pid"],
        configuration["profileDirectory"],
        configuration["chromePackageDirectory"],
    )
    return target


def target_signature(target):
    return {
        key: target[key] for key in ("address", "pid", "process_start", "at", "size")
    }


def prepare(configuration, directory):
    target = target_signature(current_target(configuration))
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    for expired in directory.glob("consent-*.json"):
        if expired.stat().st_mtime < time.time() - 60:
            expired.unlink(missing_ok=True)
    token = secrets.token_hex(16)
    path = directory / f"consent-{token}.json"
    with open(
        path, "x", opener=lambda path, flags: os.open(path, flags, 0o600)
    ) as stream:
        json.dump({"target": target, "expires": time.time() + 60}, stream)
    print(
        json.dumps(
            {
                "token": token,
                "target": target,
                "expires_in_seconds": 60,
                "requires": "Explicit user approval for this Chrome debugging connection before --approve-once",
            }
        ),
        flush=True,
    )


def consume_token(configuration, directory, token):
    if not re.fullmatch(r"[a-f0-9]{32}", token):
        raise ValueError("Invalid connection token")
    path = directory / f"consent-{token}.json"
    with path.open() as stream:
        record = json.load(stream)
    path.unlink()
    if not time.time() < record["expires"] <= time.time() + 60:
        raise RuntimeError("Connection token expired")
    target = current_target(configuration)
    if target_signature(target) != record["target"]:
        raise RuntimeError("Chrome process or window changed after preparation")
    return target


def focused_window(configuration):
    return json.loads(run_tool(configuration, "hyprctl", "-j", "activewindow")).get(
        "address"
    )


def cursor_position(configuration):
    position = json.loads(run_tool(configuration, "hyprctl", "-j", "cursorpos"))
    return position["x"], position["y"]


def focus_window(configuration, address):
    run_tool(configuration, "hyprctl", "dispatch", "focuswindow", f"address:{address}")


def move_cursor(configuration, position):
    run_tool(
        configuration,
        "hyprctl",
        "dispatch",
        "movecursor",
        *(str(value) for value in position),
    )
