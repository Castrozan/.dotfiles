import os
import socket
import tempfile
import time

APPLICATION_LAUNCHER_DAEMON_SOCKET_PATH = "/tmp/application-launcher.sock"
PICKER_VISIBLE_MILESTONE_LABEL = "picker visible"
DEFAULT_PROFILE_FILE_DEADLINE_SECONDS = 5
PROFILE_FILE_POLL_INTERVAL_SECONDS = 0.01


def make_temporary_file_path_that_does_not_yet_exist(suffix):
    file_descriptor, temporary_path = tempfile.mkstemp(suffix=suffix)
    os.close(file_descriptor)
    os.unlink(temporary_path)
    return temporary_path


def send_datagram_command_to_application_launcher_daemon(commandString):
    client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        client_socket.sendto(
            commandString.encode(), APPLICATION_LAUNCHER_DAEMON_SOCKET_PATH
        )
    finally:
        client_socket.close()


def parse_cold_start_profile_file(profile_file_path):
    milestones = []
    with open(profile_file_path) as profile_file:
        for raw_line in profile_file:
            stripped_line = raw_line.strip()
            if not stripped_line:
                continue
            elapsed_milliseconds_string, label = stripped_line.split("\t", 1)
            milestones.append((float(elapsed_milliseconds_string), label))
    return milestones


def wait_for_milestone_in_profile_file(
    profile_file_path, milestone_label, deadline_seconds
):
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        if os.path.exists(profile_file_path):
            captured_milestones = parse_cold_start_profile_file(profile_file_path)
            for elapsed_milliseconds, label in captured_milestones:
                if label == milestone_label:
                    return elapsed_milliseconds, captured_milestones
        time.sleep(PROFILE_FILE_POLL_INTERVAL_SECONDS)
    if os.path.exists(profile_file_path):
        return None, parse_cold_start_profile_file(profile_file_path)
    return None, []


def measure_one_socket_to_picker_visible_in_milliseconds():
    profile_file_path = make_temporary_file_path_that_does_not_yet_exist(
        ".cold-start.tsv"
    )
    try:
        send_datagram_command_to_application_launcher_daemon(
            f"show profile={profile_file_path}"
        )
        elapsed_milliseconds, captured_milestones = wait_for_milestone_in_profile_file(
            profile_file_path,
            PICKER_VISIBLE_MILESTONE_LABEL,
            DEFAULT_PROFILE_FILE_DEADLINE_SECONDS,
        )
        send_datagram_command_to_application_launcher_daemon("dismiss")
        return elapsed_milliseconds, captured_milestones
    finally:
        if os.path.exists(profile_file_path):
            os.unlink(profile_file_path)


def collect_discovered_display_lines_via_dump_command():
    dump_file_path = make_temporary_file_path_that_does_not_yet_exist(
        ".display-lines.txt"
    )
    try:
        send_datagram_command_to_application_launcher_daemon(
            f"dump-display-lines {dump_file_path}"
        )
        deadline = time.monotonic() + DEFAULT_PROFILE_FILE_DEADLINE_SECONDS
        while time.monotonic() < deadline:
            if os.path.exists(dump_file_path) and os.path.getsize(dump_file_path) > 0:
                break
            time.sleep(PROFILE_FILE_POLL_INTERVAL_SECONDS)
        with open(dump_file_path) as opened_dump_file:
            return [line for line in opened_dump_file.read().splitlines() if line]
    finally:
        if os.path.exists(dump_file_path):
            os.unlink(dump_file_path)
