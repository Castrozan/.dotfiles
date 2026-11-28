import json
import subprocess
import time

from ci_watcher.transient_failures import (
    RETRY_PAUSE_SECONDS,
    ConsecutiveTransientFailures,
)

RUN_VERDICT_FIELDS = "databaseId,attempt,headSha,status,conclusion,url,jobs"
WATCH_PROGRESS_SECONDS = 60


def stop_process(process):
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def _watch_once(target, output, deadline):
    process = subprocess.Popen(
        [
            "gh",
            "run",
            "watch",
            *target,
            "--compact",
            "--exit-status",
            "--interval",
            "30",
        ],
        stdout=output,
        stderr=subprocess.STDOUT,
    )
    try:
        return process.wait(timeout=max(0, deadline - time.monotonic()))
    except (KeyboardInterrupt, subprocess.TimeoutExpired):
        stop_process(process)
        raise


def _view_run(target, fields):
    response = subprocess.run(
        ["gh", "run", "view", *target, "--json", fields],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return json.loads(response.stdout)


def _completed_run_conclusion(target):
    try:
        run = _view_run(target, "status,conclusion")
    except subprocess.CalledProcessError:
        return None
    return run["conclusion"] if run["status"] == "completed" else None


def _final_status_or_none(target, watcher_status):
    if watcher_status == 0:
        return 0
    conclusion = _completed_run_conclusion(target)
    if conclusion is None:
        return None
    return 0 if conclusion == "success" else watcher_status


def _pause_before_retry(output, description, deadline):
    output.write(f"{description}; retrying\n")
    output.flush()
    time.sleep(min(RETRY_PAUSE_SECONDS, max(0, deadline - time.monotonic())))


def wait_for_run(target, directory, timeout):
    deadline = time.monotonic() + timeout
    failures = ConsecutiveTransientFailures()
    with (directory / "watch.log").open("w") as output:
        while True:
            watch_started = time.monotonic()
            watcher_status = _watch_once(target, output, deadline)
            final_status = _final_status_or_none(target, watcher_status)
            if final_status is not None:
                return final_status
            if time.monotonic() - watch_started > WATCH_PROGRESS_SECONDS:
                failures.reset()
            description = (
                f"the native watcher exited {watcher_status} before the run completed"
            )
            failures.record(description)
            _pause_before_retry(output, description, deadline)


def _view_verdict(target, directory):
    failures = ConsecutiveTransientFailures()
    deadline = time.monotonic() + RETRY_PAUSE_SECONDS * failures.limit
    with (directory / "watch.log").open("a") as output:
        while True:
            try:
                return _view_run(target, RUN_VERDICT_FIELDS)
            except subprocess.CalledProcessError as error:
                failures.record(f"reading the run verdict failed: {error}")
                _pause_before_retry(output, "reading the run verdict failed", deadline)


def retain_result(target, directory, watcher_status):
    result = _view_verdict(target, directory)
    passed = _validate_watcher_result(result, watcher_status)
    _retain_run_log(target, directory, result)
    return {**result, "outcome": "passed" if passed else "failed"}, 0 if passed else 1


def _validate_watcher_result(result, watcher_status):
    if result["status"] != "completed":
        raise RuntimeError(f"Watcher exited {watcher_status} before the run completed")
    passed = result["conclusion"] == "success"
    if passed and watcher_status != 0:
        raise RuntimeError(f"Watcher exited {watcher_status}; inspect watch.log")

    return passed


def _retain_run_log(target, directory, result):
    with (directory / "run.log").open("w") as output:
        subprocess.run(
            [
                "gh",
                "run",
                "view",
                *target,
                "--attempt",
                str(result["attempt"]),
                "--log",
            ],
            stdout=output,
            stderr=subprocess.STDOUT,
            timeout=120,
            check=True,
        )
