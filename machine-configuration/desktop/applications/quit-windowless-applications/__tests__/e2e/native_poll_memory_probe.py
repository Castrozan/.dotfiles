import gc
import json
import os
import re
import runpy
import subprocess
import sys

WARMUP_POLL_COUNT = 50
MEASURED_POLL_COUNT = 500


class PollingCompleted(Exception):
    pass


class ApplicationWithoutQuitRequests:
    def __init__(self, application):
        self.application = application

    def __getattr__(self, name):
        return getattr(self.application, name)

    def terminate(self):
        return False


def physical_footprint_bytes():
    gc.collect()
    result = subprocess.run(
        ["vmmap", "-summary", str(os.getpid())],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    footprint = re.search(
        r"^Physical footprint:\s+([\d.]+)([KMGT])", result.stdout, re.MULTILINE
    )
    return int(float(footprint[1]) * 1024 ** ("KMGT".index(footprint[2]) + 1))


def measure_polling_memory(daemon_source_path):
    daemon = runpy.run_path(daemon_source_path)
    namespace = daemon["main"].__globals__
    namespace["POLL_INTERVAL_SECONDS"] = 0.002
    discover_applications = namespace["get_running_regular_applications"]
    wait_for_next_poll = namespace[
        "wait_for_the_next_poll_while_the_workspace_receives_notifications"
    ]
    poll_count = 0
    footprints = []

    def discover_applications_without_quit_requests():
        return [
            ApplicationWithoutQuitRequests(application)
            for application in discover_applications()
        ]

    def wait_and_measure():
        nonlocal poll_count
        wait_for_next_poll()
        if poll_count in (WARMUP_POLL_COUNT, WARMUP_POLL_COUNT + MEASURED_POLL_COUNT):
            footprints.append(physical_footprint_bytes())
        if poll_count == WARMUP_POLL_COUNT + MEASURED_POLL_COUNT:
            raise PollingCompleted
        poll_count += 1

    namespace["get_running_regular_applications"] = (
        discover_applications_without_quit_requests
    )
    namespace["wait_for_the_next_poll_while_the_workspace_receives_notifications"] = (
        wait_and_measure
    )
    try:
        daemon["main"]()
    except PollingCompleted:
        pass
    return {
        "before_bytes": footprints[0],
        "after_bytes": footprints[1],
        "poll_count": MEASURED_POLL_COUNT,
    }


if __name__ == "__main__":
    print(json.dumps(measure_polling_memory(sys.argv[1])))
