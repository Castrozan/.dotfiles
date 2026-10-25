import argparse
import json
import os
import signal
import select
import subprocess
import tempfile
import time
from contextlib import ExitStack, contextmanager


def arguments_for_connection(arguments):
    parser = argparse.ArgumentParser(
        prog="chrome-devtools connect",
        description="Bounded task-owned connection; native approval requires explicit consent for this attempt.",
    )
    parser.add_argument("--timeout", type=int, default=20, choices=range(3, 31))
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--prepare",
        action="store_true",
        help="Identify Chrome and issue a 60-second attempt token without connecting",
    )
    group.add_argument(
        "--approve-once",
        metavar="TOKEN",
        help="Consume the prepared token only after explicit approval for this connection",
    )
    return parser.parse_args(arguments)


def finish_process(process, group=False):
    if process.poll() is None:
        if group:
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        try:
            process.wait(timeout=6 if group else 1)
        except subprocess.TimeoutExpired:
            if group:
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.wait(timeout=1)
    if process.stdout is not None:
        process.stdout.close()


def remaining_time(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise RuntimeError(
            "Connection deadline expired; request scoped approval before retrying a new grant"
        )
    return remaining


def start_consent_helper(configuration, session, token, deadline, stack):
    if not configuration.consent_helper:
        raise RuntimeError("Native consent is supported only on Hyprland Linux")
    helper = subprocess.Popen(
        [
            *configuration.consent_helper,
            "watch",
            str(session.directory / session.identifier),
            token,
            str(remaining_time(deadline)),
        ],
        stdout=subprocess.PIPE,
        start_new_session=True,
        text=True,
    )
    stack.callback(finish_process, helper, True)
    ready, _, _ = select.select(
        [helper.stdout], [], [], min(5, remaining_time(deadline))
    )
    if not ready or helper.stdout.readline().strip() != "ready":
        raise RuntimeError("Native consent helper could not arm safely")
    return helper


def verified_pages(output):
    try:
        result = json.loads(output)
    except ValueError:
        return False
    return (
        isinstance(result, dict)
        and isinstance(result.get("pages"), list)
        and bool(result["pages"])
    )


def request_pages(configuration, session, deadline, helper, stack):
    with tempfile.TemporaryFile(mode="w+") as output:
        process = subprocess.Popen(
            [
                configuration.upstream_executable,
                "--sessionId",
                session.identifier,
                "list_pages",
                "--output-format",
                "json",
            ],
            stdout=output,
            stderr=output,
        )
        stack.callback(finish_process, process)
        while process.poll() is None:
            remaining_time(deadline)
            if helper is not None and helper.poll() not in (None, 0):
                raise RuntimeError(
                    "Native consent helper rejected this attempt; no retry was made"
                )
            time.sleep(min(0.05, remaining_time(deadline)))
        output.seek(0)
        response = output.read()
        print(response, end="", flush=True)
        if process.returncode or not verified_pages(response):
            raise RuntimeError("Chrome did not return a verified nonempty page list")
        return 0


def interrupted(signum, frame):
    raise InterruptedError("Connection attempt cancelled")


@contextmanager
def cancellable():
    previous = {
        value: signal.signal(value, interrupted)
        for value in (signal.SIGTERM, signal.SIGINT)
    }
    try:
        yield
    finally:
        for value, handler in previous.items():
            signal.signal(value, handler)


def connect(configuration, session, arguments, start_worker, stop_worker):
    options = arguments_for_connection(arguments)
    if options.prepare:
        if not configuration.consent_helper:
            raise RuntimeError(
                "Native consent preparation is supported only on Hyprland Linux"
            )
        return subprocess.run(
            [
                *configuration.consent_helper,
                "prepare",
                str(session.directory / session.identifier),
            ],
            check=False,
            timeout=5,
        ).returncode
    deadline = time.monotonic() + options.timeout
    if options.approve_once and session.mode() == "headless":
        raise ValueError(
            "A native approval token cannot be used with a headless worker"
        )
    with session.attached_locked(), session.locked(), cancellable():
        request_started = False
        try:
            with ExitStack() as stack:
                helper = (
                    start_consent_helper(
                        configuration, session, options.approve_once, deadline, stack
                    )
                    if options.approve_once
                    else None
                )
                request_started = True
                if not session.running():
                    result = start_worker(
                        configuration,
                        session,
                        session.mode(),
                        timeout=remaining_time(deadline),
                    )
                    if result:
                        raise RuntimeError("Chrome worker failed to start")
                return request_pages(configuration, session, deadline, helper, stack)
        except BaseException:
            if not request_started:
                raise
            try:
                result = stop_worker(configuration, session, timeout=5)
                if result:
                    raise RuntimeError(f"Worker stop exited with status {result}")
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                print(
                    f"Owned worker cleanup failed: {error}; run chrome-devtools stop",
                    flush=True,
                )
            raise
