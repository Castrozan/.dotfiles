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


def send_disk_alert_email_best_effort(level, free_gigabytes, disk_guard):
    if not disk_alert_email_configured(disk_guard):
        log("disk-guard email not configured; alert logged only")
        return True
    try:
        app_password = read_smtp_app_password(disk_guard["app_password_file"])
        if not app_password:
            log("disk-guard email skipped; smtp app password empty")
            return True
        message = build_disk_alert_message(level, free_gigabytes, disk_guard)
        with smtplib.SMTP(
            disk_guard["smtp_host"], disk_guard["smtp_port"], timeout=30
        ) as server:
            server.starttls()
            server.login(disk_guard["smtp_username"], app_password)
            server.send_message(message)
        log(f"disk-guard alert email sent ({level})")
        return True
    except Exception as error:
        log(f"disk-guard alert email failed ({level}): {error}")
        return False
