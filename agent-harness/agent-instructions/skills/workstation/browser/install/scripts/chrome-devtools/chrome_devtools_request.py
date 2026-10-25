import json
import os
import select
import signal
import subprocess
import tempfile
import time


def signal_process(process, group, requested_signal):
    if group:
        os.killpg(process.pid, requested_signal)
    elif requested_signal == signal.SIGTERM:
        process.terminate()
    else:
        process.kill()


def finish_process(process, group=False):
    if process.poll() is None:
        signal_process(process, group, signal.SIGTERM)
        try:
            process.wait(timeout=6 if group else 1)
        except subprocess.TimeoutExpired:
            signal_process(process, group, signal.SIGKILL)
            process.wait(timeout=1)
    if process.stdout is not None:
        process.stdout.close()


def helper_failed(helper):
    return helper is not None and helper.poll() not in (None, 0)


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
            if helper_failed(helper):
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
