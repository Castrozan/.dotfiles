import fcntl
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
from contextlib import contextmanager
from pathlib import Path

from opencli_owner import register_process
from opencli_processes import stop_process, wait_for_bridge


def profile_directory(name):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}", name):
        raise ValueError(
            "Use a profile name containing letters, digits, dots, dashes or underscores"
        )
    root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return root / "opencli/profiles" / name


def prepare_extension(profile, token):
    destination = profile / "OpenCLIBridge"
    destination.mkdir(exist_ok=True, mode=0o700)
    destination.chmod(0o700)
    shutil.copytree(os.environ["OPENCLI_EXTENSION"], destination, dirs_exist_ok=True)
    destination.chmod(0o700)
    for path in destination.rglob("*"):
        path.chmod(0o700 if path.is_dir() else 0o600)
    background = destination / "dist/background.js"
    source = background.read_text()
    marker = "new WebSocket(DAEMON_WS_URL)"
    if source.count(marker) != 1:
        raise RuntimeError("The packaged Browser Bridge WebSocket contract changed")
    source = source.replace(
        marker,
        "new WebSocket(DAEMON_WS_URL + '?token=' + encodeURIComponent((await (await fetch(chrome.runtime.getURL('job-token.json'), {cache: 'no-store'})).json()).token))",
    )
    background.write_text(source)
    credential = destination / "job-token.json"
    credential.write_text(json.dumps({"token": token}))
    credential.chmod(0o600)
    return destination


def require_unused_port():
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            listener.bind(("127.0.0.1", 19825))
        except OSError as error:
            raise RuntimeError(
                "OpenCLI port 19825 is already owned by another process"
            ) from error


def browser_arguments(profile, extension, headed):
    arguments = [
        os.environ["OPENCLI_BROWSER"],
        f"--user-data-dir={profile}",
        f"--load-extension={extension}",
        f"--disable-extensions-except={extension}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-sync",
        "--password-store=basic",
        "--window-size=1280,900",
    ]
    if not headed:
        arguments.append("--headless=new")
    return [*arguments, "about:blank"]


@contextmanager
def browser_job(name, headed=False):
    profile = profile_directory(name)
    profile.mkdir(parents=True, exist_ok=True, mode=0o700)
    profile.chmod(0o700)
    state = (
        Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "opencli"
    )
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    state.chmod(0o700)
    with open(state / "job.lock", "a", opener=private_opener) as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError(
                "Another OpenCLI job owns the Bridge; retry after it finishes"
            ) from error
        require_unused_port()
        token = secrets.token_urlsafe(32)
        extension = prepare_extension(profile, token)
        processes = []
        environment = dict(
            os.environ,
            OPENCLI_BRIDGE_TOKEN=token,
            OPENCLI_JOB_SCOPE=str(profile),
            OPENCLI_JOB_IDENTIFIER=secrets.token_hex(16),
        )
        for key in ("OPENCLI_CDP_ENDPOINT", "OPENCLI_CDP_TARGET", "OPENCLI_PROFILE"):
            environment.pop(key, None)
        try:
            with open(state / "last-job.log", "w", opener=private_opener) as output:
                os.fchmod(output.fileno(), 0o600)
                for arguments in (
                    [os.environ["OPENCLI_NODE"], os.environ["OPENCLI_DAEMON"]],
                    browser_arguments(profile, extension, headed),
                ):
                    processes.append(
                        subprocess.Popen(
                            arguments,
                            env=dict(environment),
                            stdout=output,
                            stderr=output,
                            start_new_session=True,
                        )
                    )
                    register_process(processes[-1])
                wait_for_bridge(processes)
                yield environment
        finally:
            for process in reversed(processes):
                stop_process(process)
            shutil.rmtree(extension, ignore_errors=True)


def private_opener(path, flags):
    return os.open(path, flags, 0o600)
