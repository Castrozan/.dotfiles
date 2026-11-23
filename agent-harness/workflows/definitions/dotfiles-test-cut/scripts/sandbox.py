import os
import shutil
import subprocess
import sys

SANDBOX_PROGRAM = "bwrap"
SYSTEM_PROFILE = "/run/current-system"
HOST_TEMPORARY_DIRECTORY = "/tmp"  # noqa: S108


class SandboxUnavailable(RuntimeError):
    pass


def sandbox_program():
    program = shutil.which(SANDBOX_PROGRAM)
    if program is None:
        raise SandboxUnavailable(
            "mutated code runs only inside bubblewrap, and bwrap is not on PATH"
        )
    return program


def bindings(root, writable_directories):
    system_profile = (
        ["--ro-bind", SYSTEM_PROFILE, SYSTEM_PROFILE]
        if os.path.exists(SYSTEM_PROFILE)
        else []
    )
    writable = [
        argument
        for directory in [root, *writable_directories]
        for argument in ("--bind", str(directory), str(directory))
    ]
    return [
        "--ro-bind",
        "/",
        "/",
        "--dev",
        "/dev",
        "--proc",
        "/proc",
        "--tmpfs",
        HOST_TEMPORARY_DIRECTORY,
        "--tmpfs",
        "/run",
        *system_profile,
        *writable,
    ]


def environment(extra_environment):
    variables = {
        "PATH": os.environ["PATH"],
        "HOME": HOST_TEMPORARY_DIRECTORY,
        "PYTHONDONTWRITEBYTECODE": "1",
    } | extra_environment
    return [
        argument
        for name, value in variables.items()
        for argument in ("--setenv", name, value)
    ]


def sandboxed_pytest(
    root, arguments, timeout_seconds, writable_directories=(), extra_environment=None
):
    return subprocess.run(
        [
            sandbox_program(),
            *bindings(root, writable_directories),
            "--unshare-net",
            "--unshare-ipc",
            "--unshare-pid",
            "--die-with-parent",
            "--new-session",
            "--clearenv",
            *environment(extra_environment or {}),
            "--chdir",
            str(root),
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            *arguments,
        ],
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
