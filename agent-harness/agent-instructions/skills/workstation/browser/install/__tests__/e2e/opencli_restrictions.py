import signal
import socket
import subprocess
import sys
import time

from opencli_fixture import clean


def verify_restrictions(runner, root, profile, environment):
    checks = {}
    for name, arguments in [
        ("command_failure", ["--", sys.executable, "-c", "raise SystemExit(7)"]),
        (
            "timeout",
            [
                "--timeout",
                "1",
                "--",
                sys.executable,
                "-c",
                "import time; time.sleep(30)",
            ],
        ),
    ]:
        result = subprocess.run(
            [runner, "--profile", profile, *arguments],
            capture_output=True,
            text=True,
            timeout=70,
            env=environment,
        )
        checks[f"{name}_returns_failure"] = result.returncode != 0
        checks[f"zero_owned_processes_after_{name}"] = clean()
    for number in [signal.SIGTERM, signal.SIGKILL]:
        marker = root / f"active-{number}"
        marker.unlink(missing_ok=True)
        process = subprocess.Popen(
            [
                runner,
                "--profile",
                profile,
                "--",
                sys.executable,
                "-c",
                "import pathlib,time,sys; pathlib.Path(sys.argv[1]).write_text('active'); time.sleep(120)",
                str(marker),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=environment,
        )
        try:
            deadline = time.monotonic() + 50
            while (
                not marker.exists()
                and time.monotonic() < deadline
                and process.poll() is None
            ):
                time.sleep(0.1)
            assert marker.exists(), f"Job failed to start before signal {number}"
            if number == signal.SIGTERM:
                other = subprocess.run(
                    [
                        runner,
                        "--profile",
                        "competing",
                        "--",
                        sys.executable,
                        "-c",
                        "raise SystemExit(0)",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=45,
                    env=environment,
                )
                checks["competing_job_refused_without_interrupting_owner"] = (
                    other.returncode != 0 and process.poll() is None
                )
            process.send_signal(number)
            process.wait(timeout=25)
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=25)
        checks[f"zero_owned_processes_after_signal_{number}"] = clean()
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 19825))
        listener.listen(1)
        result = subprocess.run(
            [
                runner,
                "--profile",
                profile,
                "--",
                sys.executable,
                "-c",
                "raise SystemExit(0)",
            ],
            capture_output=True,
            text=True,
            timeout=45,
            env=environment,
        )
        checks["existing_service_not_adopted"] = (
            result.returncode != 0 and listener.getsockname()[1] == 19825
        )
    return checks
