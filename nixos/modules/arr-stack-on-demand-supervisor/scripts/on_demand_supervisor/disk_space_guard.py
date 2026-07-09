import json
import os

from disk_alert_email import send_disk_alert_email_best_effort
from download_chain_control import stop_on_demand_services
from runtime_environment import log


def free_gigabytes_available(path):
    stats = os.statvfs(path)
    return stats.f_bavail * stats.f_frsize / (1024**3)


def classify_free_space(free_gigabytes, warning_gigabytes, critical_gigabytes):
    if free_gigabytes < critical_gigabytes:
        return "critical"
    if free_gigabytes < warning_gigabytes:
        return "warning"
    return "ok"


def read_alert_state(alert_state_file_path):
    try:
        with open(alert_state_file_path, encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, ValueError):
        return {"level": "ok", "last_alert_epoch": 0.0}


def write_alert_state(alert_state_file_path, level, now_epoch):
    with open(alert_state_file_path, "w", encoding="utf-8") as handle:
        json.dump({"level": level, "last_alert_epoch": now_epoch}, handle)


def alert_is_due(level, previous_state, now_epoch, critical_reminder_seconds):
    previous_level = previous_state.get("level", "ok")
    if level != previous_level:
        return True
    if level == "critical":
        return (
            now_epoch - previous_state.get("last_alert_epoch", 0.0)
            >= critical_reminder_seconds
        )
    return False


def enforce_disk_space_guard(disk_guard, base_command, now_epoch, dry_run):
    free_gigabytes = free_gigabytes_available(disk_guard["path"])
    level = classify_free_space(
        free_gigabytes,
        disk_guard["warning_gigabytes"],
        disk_guard["critical_gigabytes"],
    )
    held_down_services = []
    if level == "critical":
        held_down_services = [disk_guard["fill_service"]]
        log(
            f"disk-guard CRITICAL: {free_gigabytes:.1f}G free below "
            f"{disk_guard['critical_gigabytes']}G; stopping {disk_guard['fill_service']}"
        )
        stop_on_demand_services(base_command, [disk_guard["fill_service"]], dry_run)
    elif level == "warning":
        log(
            f"disk-guard warning: {free_gigabytes:.1f}G free below "
            f"{disk_guard['warning_gigabytes']}G"
        )
    previous_state = read_alert_state(disk_guard["alert_state_file"])
    if alert_is_due(
        level, previous_state, now_epoch, disk_guard["critical_reminder_seconds"]
    ):
        record_disk_alert(disk_guard, level, free_gigabytes, now_epoch, dry_run)
    return held_down_services


def record_disk_alert(disk_guard, level, free_gigabytes, now_epoch, dry_run):
    if dry_run:
        log(f"[dry-run] would email disk {level} alert and persist alert state")
        return
    alert_sent = send_disk_alert_email_best_effort(level, free_gigabytes, disk_guard)
    last_alert_epoch = now_epoch if alert_sent else 0.0
    write_alert_state(disk_guard["alert_state_file"], level, last_alert_epoch)
