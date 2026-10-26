import argparse
import signal
import subprocess
import time
from contextlib import ExitStack, contextmanager

from chrome_devtools_request import remaining_time, request_pages, start_consent_helper


def arguments_for_connection(arguments):
    parser = argparse.ArgumentParser(
        prog="chrome-devtools connect",
        description="Bounded task-owned connection to Chrome Global.",
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
        help="Consume the prepared token so the native helper accepts Chrome's Allow prompt",
    )
    group.add_argument(
        "--manual-once",
        action="store_true",
        help="Request one new connection whose Allow prompt the caller accepts",
    )
    return parser.parse_args(arguments)


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


def prepare_connection(configuration, session):
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


def validate_approval_mode(session, options):
    if session.mode() != "headless":
        return
    if options.approve_once:
        raise ValueError(
            "A native approval token cannot be used with a headless worker"
        )
    if options.manual_once:
        raise ValueError("Manual consent cannot be used with a headless worker")


def require_connection_authorization(configuration, session, options):
    if session.mode() == "headless":
        return
    if options.approve_once:
        return
    if options.manual_once:
        return
    if not session.running():
        raise RuntimeError(
            "A new attached connection needs connect --prepare then --approve-once, "
            "or --manual-once"
        )
    session.require_current_worker(configuration.upstream_executable)


def restart_approved_worker(configuration, session, options, deadline, stop_worker):
    if not (options.approve_once or options.manual_once):
        return
    if not session.running():
        return
    if stop_worker(configuration, session, timeout=min(5, remaining_time(deadline))):
        raise RuntimeError(
            "Previous owned worker could not stop for the approved connection"
        )


def connection_helper(configuration, session, token, deadline, stack):
    if not token:
        return None
    return start_consent_helper(configuration, session, token, deadline, stack)


def ensure_connection_worker(configuration, session, deadline, start_worker):
    if session.running():
        return
    result = start_worker(
        configuration, session, session.mode(), timeout=remaining_time(deadline)
    )
    if result:
        raise RuntimeError("Chrome worker failed to start")


def cleanup_failed_request(configuration, session, request_started, stop_worker):
    if not request_started:
        return
    try:
        result = stop_worker(configuration, session, timeout=5)
        if result:
            raise RuntimeError(f"Worker stop exited with status {result}")
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(
            f"Owned worker cleanup failed: {error}; run chrome-devtools stop",
            flush=True,
        )


def connect(configuration, session, arguments, start_worker, stop_worker):
    options = arguments_for_connection(arguments)
    if options.prepare:
        return prepare_connection(configuration, session)
    deadline = time.monotonic() + options.timeout
    validate_approval_mode(session, options)
    with session.attached_locked(), session.locked(), cancellable():
        require_connection_authorization(configuration, session, options)
        restart_approved_worker(configuration, session, options, deadline, stop_worker)
        request_started = False
        try:
            with ExitStack() as stack:
                helper = connection_helper(
                    configuration, session, options.approve_once, deadline, stack
                )
                request_started = True
                ensure_connection_worker(configuration, session, deadline, start_worker)
                return request_pages(configuration, session, deadline, helper, stack)
        except BaseException:
            cleanup_failed_request(configuration, session, request_started, stop_worker)
            raise
