from __future__ import annotations

import re
import subprocess

import psutil

CHROME_APPLICATION_BINARY_PATH = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)
SUBPROCESS_QUERY_TIMEOUT_SECONDS = 15.0

CHROME_VERSION_REPORT_PATTERN = re.compile(r"([0-9]+(?:\.[0-9]+)+)")
FRAMEWORK_VERSION_IN_EXECUTABLE_PATH_PATTERN = re.compile(
    r"Google Chrome Framework\.framework/Versions/([0-9][0-9.]*)"
)


def extract_chrome_version_from_version_report(version_report: str) -> str | None:
    match = CHROME_VERSION_REPORT_PATTERN.search(version_report)
    return match.group(1) if match else None


def extract_framework_version_from_executable_path(
    executable_path: str,
) -> str | None:
    match = FRAMEWORK_VERSION_IN_EXECUTABLE_PATH_PATTERN.search(executable_path)
    return match.group(1) if match else None


def running_versions_have_drifted_from_on_disk(
    on_disk_version: str, running_framework_versions: set[str]
) -> bool:
    return any(version != on_disk_version for version in running_framework_versions)


def read_on_disk_chrome_version() -> str | None:
    try:
        completed_process = subprocess.run(
            [CHROME_APPLICATION_BINARY_PATH, "--version"],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_QUERY_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return extract_chrome_version_from_version_report(completed_process.stdout)


def collect_running_framework_versions(processes) -> set[str]:
    running_framework_versions: set[str] = set()
    for process in processes:
        try:
            executable_path = process.exe()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        framework_version = extract_framework_version_from_executable_path(
            executable_path
        )
        if framework_version is not None:
            running_framework_versions.add(framework_version)
    return running_framework_versions
