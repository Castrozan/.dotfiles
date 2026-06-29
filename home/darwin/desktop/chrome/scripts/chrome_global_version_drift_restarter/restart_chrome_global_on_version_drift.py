from __future__ import annotations

import argparse

from chrome_global_processes import find_chrome_global_processes
from chrome_global_restart import restart_chrome_global
from chrome_version_detection import (
    collect_running_framework_versions,
    read_on_disk_chrome_version,
    running_versions_have_drifted_from_on_disk,
)
from drift_observation_state import (
    CONSECUTIVE_DRIFT_OBSERVATIONS_BEFORE_RESTART,
    DRIFT_OBSERVATION_STATE_FILE_PATH,
    read_consecutive_drift_observation_count,
    should_restart_after_observation,
    write_consecutive_drift_observation_count,
)
from frontmost_application import chrome_is_the_frontmost_application
from restarter_log import log_event


def parse_command_line_arguments() -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--launcher-binary", required=True)
    return argument_parser.parse_args()


def main() -> None:
    command_line_arguments = parse_command_line_arguments()

    on_disk_version = read_on_disk_chrome_version()
    if on_disk_version is None:
        log_event("could not read on-disk Chrome version; skipping")
        return

    chrome_global_processes = find_chrome_global_processes()
    if not chrome_global_processes:
        write_consecutive_drift_observation_count(DRIFT_OBSERVATION_STATE_FILE_PATH, 0)
        return

    running_framework_versions = collect_running_framework_versions(
        chrome_global_processes
    )
    if not running_versions_have_drifted_from_on_disk(
        on_disk_version, running_framework_versions
    ):
        write_consecutive_drift_observation_count(DRIFT_OBSERVATION_STATE_FILE_PATH, 0)
        return

    if chrome_is_the_frontmost_application():
        log_event(
            f"version drift detected (on-disk={on_disk_version} "
            f"running={sorted(running_framework_versions)}) "
            "but Chrome is frontmost; deferring restart"
        )
        return

    consecutive_drift_observations = (
        read_consecutive_drift_observation_count(DRIFT_OBSERVATION_STATE_FILE_PATH) + 1
    )
    if not should_restart_after_observation(
        consecutive_drift_observations, CONSECUTIVE_DRIFT_OBSERVATIONS_BEFORE_RESTART
    ):
        log_event(
            f"version drift observation {consecutive_drift_observations}/"
            f"{CONSECUTIVE_DRIFT_OBSERVATIONS_BEFORE_RESTART} "
            f"(on-disk={on_disk_version} "
            f"running={sorted(running_framework_versions)})"
        )
        write_consecutive_drift_observation_count(
            DRIFT_OBSERVATION_STATE_FILE_PATH, consecutive_drift_observations
        )
        return

    restart_succeeded = restart_chrome_global(
        command_line_arguments.launcher_binary,
        on_disk_version,
        running_framework_versions,
    )
    write_consecutive_drift_observation_count(
        DRIFT_OBSERVATION_STATE_FILE_PATH,
        0 if restart_succeeded else consecutive_drift_observations,
    )


if __name__ == "__main__":
    main()
