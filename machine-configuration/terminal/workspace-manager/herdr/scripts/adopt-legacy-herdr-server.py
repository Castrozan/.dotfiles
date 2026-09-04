import json
import os
import pathlib
import signal
import subprocess
import sys
import time


def run_command(*arguments, check=False, timeout=None):
    return subprocess.run(
        arguments,
        check=check,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def unit_is_active(unit_name):
    result = run_command(
        os.environ["HERDR_SYSTEMCTL"],
        "--user",
        "is-active",
        "--quiet",
        unit_name,
    )
    return result.returncode == 0


def unit_property(unit_name, property_name):
    result = run_command(
        os.environ["HERDR_SYSTEMCTL"],
        "--user",
        "show",
        unit_name,
        f"--property={property_name}",
        "--value",
        check=True,
    )
    return result.stdout.strip()


def process_exists(process_id):
    return pathlib.Path(f"/proc/{process_id}").exists()


def legacy_process_ids():
    control_group = unit_property(
        os.environ["HERDR_LEGACY_UNIT"],
        "ControlGroup",
    )
    if not control_group or control_group == "/":
        return []
    control_group_path = pathlib.Path("/sys/fs/cgroup") / control_group.lstrip("/")
    process_ids = set()
    for process_file in control_group_path.rglob("cgroup.procs"):
        process_ids.update(
            int(line) for line in process_file.read_text().splitlines() if line
        )
    return sorted(process_ids)


def attach_process_to_herdr_service(process_id):
    result = run_command(
        os.environ["HERDR_BUSCTL"],
        "--user",
        "call",
        "org.freedesktop.systemd1",
        "/org/freedesktop/systemd1",
        "org.freedesktop.systemd1.Manager",
        "AttachProcessesToUnit",
        "ssau",
        os.environ["HERDR_TARGET_UNIT"],
        "",
        "1",
        str(process_id),
    )
    if result.returncode != 0 and process_exists(process_id):
        raise RuntimeError(result.stderr.strip())


def prepare_handoff_import():
    legacy_server_process_id = int(os.environ["HERDR_LEGACY_SERVER_PID"])
    importer_process_id = os.getppid()
    attach_process_to_herdr_service(importer_process_id)
    for process_id in legacy_process_ids():
        if process_id not in {legacy_server_process_id, importer_process_id}:
            attach_process_to_herdr_service(process_id)


def herdr_server_is_running():
    result = run_command(
        os.environ["HERDR_EXECUTABLE"],
        "session",
        "list",
        "--json",
    )
    if result.returncode != 0:
        return False
    sessions = json.loads(result.stdout).get("sessions", [])
    return any(session.get("running") for session in sessions)


def wait_for_legacy_unit_stop(legacy_unit, timeout_seconds=30):
    deadline = time.monotonic() + timeout_seconds
    while unit_is_active(legacy_unit):
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.25)
    return True


def adopt_legacy_server():
    legacy_unit = os.environ["HERDR_LEGACY_UNIT"]
    target_unit = os.environ["HERDR_TARGET_UNIT"]
    if not unit_is_active(legacy_unit):
        return
    if not unit_is_active(target_unit):
        raise RuntimeError(f"{target_unit} is not active")
    coordinator_process_id = int(unit_property(target_unit, "MainPID"))
    os.kill(coordinator_process_id, signal.SIGSTOP)
    try:
        run_command(
            os.environ["HERDR_EXECUTABLE"],
            "server",
            "live-handoff",
            "--import-exe",
            os.environ["HERDR_IMPORT_EXECUTABLE"],
            check=True,
            timeout=60,
        )
    finally:
        if process_exists(coordinator_process_id):
            os.kill(coordinator_process_id, signal.SIGCONT)
    if not herdr_server_is_running():
        raise RuntimeError("herdr server is unavailable after legacy adoption")
    if not wait_for_legacy_unit_stop(legacy_unit):
        raise RuntimeError(f"{legacy_unit} remained active after legacy adoption")
    run_command(
        os.environ["HERDR_RECONCILER"],
        "record-active",
        check=True,
    )


def main():
    operation = sys.argv[1]
    if operation == "prepare-import":
        prepare_handoff_import()
        return
    if operation == "adopt":
        adopt_legacy_server()
        return
    raise RuntimeError(f"unsupported operation: {operation}")


if __name__ == "__main__":
    main()
