import os

from disk_alert_email import send_mount_alert_email_best_effort
from disk_space_guard import read_alert_state, write_alert_state
from download_chain_control import stop_on_demand_services
from runtime_environment import log


def data_mount_is_healthy(path):
    try:
        if not os.path.ismount(path):
            return False
        os.statvfs(path)
        os.listdir(path)
    except OSError:
        return False
    return True


def mount_alert_is_due(previous_state, now_epoch, reminder_seconds):
    if previous_state.get("level") != "lost":
        return True
    return now_epoch - previous_state.get("last_alert_epoch", 0.0) >= reminder_seconds


def stop_stack_best_effort(base_command, on_demand_services, dry_run):
    try:
        stop_on_demand_services(base_command, on_demand_services, dry_run)
    except Exception as error:
        log(
            f"mount-guard: best-effort stop failed (docker may already be down): {error}"
        )


def record_mount_alert(disk_guard, now_epoch, dry_run):
    if dry_run:
        log("[dry-run] would email data-drive-lost alert and persist mount alert state")
        return
    alert_sent = send_mount_alert_email_best_effort(disk_guard)
    last_alert_epoch = now_epoch if alert_sent else 0.0
    write_alert_state(disk_guard["mount_alert_state_file"], "lost", last_alert_epoch)


def clear_mount_alert_state_on_recovery(disk_guard, now_epoch, dry_run):
    previous_state = read_alert_state(disk_guard["mount_alert_state_file"])
    if previous_state.get("level") == "lost":
        log(
            f"mount-guard: {disk_guard['path']} is a healthy mount again; clearing alert state"
        )
        if not dry_run:
            write_alert_state(disk_guard["mount_alert_state_file"], "ok", now_epoch)


def enforce_data_mount_guard(configuration, base_command, now_epoch, dry_run):
    disk_guard = configuration.get("disk_guard")
    if not disk_guard or not disk_guard.get("mount_guard_enabled"):
        return False
    if data_mount_is_healthy(disk_guard["path"]):
        clear_mount_alert_state_on_recovery(disk_guard, now_epoch, dry_run)
        return False
    log(
        f"mount-guard: data mount {disk_guard['path']} is not a healthy drive mount; "
        "holding the stack down"
    )
    stop_stack_best_effort(base_command, configuration["on_demand_services"], dry_run)
    previous_state = read_alert_state(disk_guard["mount_alert_state_file"])
    if mount_alert_is_due(
        previous_state, now_epoch, disk_guard["critical_reminder_seconds"]
    ):
        record_mount_alert(disk_guard, now_epoch, dry_run)
    return True
