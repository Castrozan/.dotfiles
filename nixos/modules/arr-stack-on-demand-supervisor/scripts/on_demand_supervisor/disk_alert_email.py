import smtplib
from email.message import EmailMessage

from runtime_environment import log


def disk_alert_email_configured(disk_guard):
    return bool(disk_guard.get("app_password_file")) and bool(
        disk_guard.get("smtp_username")
    )


def read_smtp_app_password(app_password_file_path):
    with open(app_password_file_path, encoding="utf-8") as handle:
        return handle.read().strip()


def build_disk_alert_message(level, free_gigabytes, disk_guard):
    message = EmailMessage()
    message["Subject"] = (
        f"[arr-stack] disk {level}: {free_gigabytes:.1f} GiB free on chise"
    )
    message["From"] = disk_guard["email_sender"]
    message["To"] = disk_guard["email_recipient"]
    body = (
        f"The arr-stack disk-space guard on chise reports {level}.\n"
        f"Free on {disk_guard['path']}: {free_gigabytes:.1f} GiB "
        f"(warning {disk_guard['warning_gigabytes']} GiB, "
        f"critical {disk_guard['critical_gigabytes']} GiB).\n"
    )
    if level == "critical":
        body += (
            f"{disk_guard['fill_service']} was stopped to halt further disk fill; "
            "it resumes automatically once free space recovers.\n"
        )
    message.set_content(body)
    return message


def deliver_alert_message_best_effort(build_message, disk_guard, context_label):
    if not disk_alert_email_configured(disk_guard):
        log(f"{context_label} email not configured; alert logged only")
        return True
    try:
        app_password = read_smtp_app_password(disk_guard["app_password_file"])
        if not app_password:
            log(f"{context_label} email skipped; smtp app password empty")
            return True
        message = build_message()
        with smtplib.SMTP(
            disk_guard["smtp_host"], disk_guard["smtp_port"], timeout=30
        ) as server:
            server.starttls()
            server.login(disk_guard["smtp_username"], app_password)
            server.send_message(message)
        log(f"{context_label} email sent")
        return True
    except Exception as error:
        log(f"{context_label} email failed: {error}")
        return False


def send_disk_alert_email_best_effort(level, free_gigabytes, disk_guard):
    return deliver_alert_message_best_effort(
        lambda: build_disk_alert_message(level, free_gigabytes, disk_guard),
        disk_guard,
        f"disk-guard alert ({level})",
    )


def build_mount_alert_message(disk_guard):
    message = EmailMessage()
    message["Subject"] = "[arr-stack] data drive disconnected on chise"
    message["From"] = disk_guard["email_sender"]
    message["To"] = disk_guard["email_recipient"]
    message.set_content(
        "The arr-stack data drive is no longer a healthy mount at "
        f"{disk_guard['path']} on chise.\n"
        "The stack was held down to avoid thrashing on a dead mount or writing to the "
        "root disk. Reconnect the drive and bring the stack back up.\n"
    )
    return message


def send_mount_alert_email_best_effort(disk_guard):
    return deliver_alert_message_best_effort(
        lambda: build_mount_alert_message(disk_guard),
        disk_guard,
        "mount-guard alert",
    )
