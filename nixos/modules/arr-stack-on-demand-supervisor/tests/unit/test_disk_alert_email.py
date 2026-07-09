import sys
from pathlib import Path

SUPERVISOR_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "on_demand_supervisor"
)
sys.path.insert(0, str(SUPERVISOR_PACKAGE_DIRECTORY_PATH))

import disk_alert_email


def disk_guard_with(app_password_file="/run/agenix/secret", smtp_username="user@x"):
    return {
        "path": "/home/zanoni/arr-stack",
        "warning_gigabytes": 30,
        "critical_gigabytes": 15,
        "fill_service": "qbittorrent",
        "app_password_file": app_password_file,
        "smtp_username": smtp_username,
        "email_sender": "user@x",
        "email_recipient": "lucas@x",
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
    }


def test_email_configured_requires_both_password_file_and_username():
    assert disk_alert_email.disk_alert_email_configured(disk_guard_with()) is True
    assert (
        disk_alert_email.disk_alert_email_configured(
            disk_guard_with(app_password_file="")
        )
        is False
    )
    assert (
        disk_alert_email.disk_alert_email_configured(disk_guard_with(smtp_username=""))
        is False
    )


def test_critical_message_carries_level_size_and_fill_service_resume_line():
    message = disk_alert_email.build_disk_alert_message(
        "critical", 4.2, disk_guard_with()
    )
    assert "critical" in message["Subject"]
    assert "4.2 GiB" in message["Subject"]
    assert message["To"] == "lucas@x"
    body = message.get_content()
    assert "qbittorrent was stopped" in body


def test_warning_message_omits_the_resume_line():
    message = disk_alert_email.build_disk_alert_message(
        "warning", 22.0, disk_guard_with()
    )
    body = message.get_content()
    assert "was stopped" not in body


def test_send_returns_true_when_email_not_configured():
    assert (
        disk_alert_email.send_disk_alert_email_best_effort(
            "critical", 4.2, disk_guard_with(app_password_file="")
        )
        is True
    )
