from email.message import EmailMessage
from pathlib import Path

from disk_alert_email import deliver_alert_message_best_effort
from download_chain_control import read_last_active_epoch, write_last_active_epoch
from missing_search_api import queued_records
from runtime_environment import log, read_arr_api_key_from_config_xml

IMPORT_ALERT_INTERVAL_SECONDS = 86400


def blocked_download_lines(configuration):
    lines = []
    for application in ("radarr", "sonarr"):
        base_url = configuration[f"{application}_url"]
        api_key = read_arr_api_key_from_config_xml(
            configuration[f"{application}_config_file"]
        )
        records = queued_records(base_url, api_key)
        if records is None:
            log(f"import-alert: {application} queue unavailable")
            continue
        seen = set()
        for record in records:
            messages = [
                message
                for status in record.get("statusMessages", [])
                for message in status.get("messages", [])
            ]
            if not messages:
                continue
            identity = record.get("downloadId") or record.get("id")
            if identity in seen:
                continue
            seen.add(identity)
            size = (record.get("size") or 0) / 1024**3
            lines.append(
                f"{application}: {record.get('title', 'Unknown release')} ({size:.1f} GiB): {'; '.join(messages)}\n{base_url}/activity/queue"
            )
    return lines


def build_import_alert(lines, delivery):
    message = EmailMessage()
    message["Subject"] = f"[arr-stack] {len(lines)} downloads need attention"
    message["From"] = delivery["email_sender"]
    message["To"] = delivery["email_recipient"]
    message.set_content(
        "These downloads occupy disk space but ARR cannot import them. Open Activity > Queue with Show Unknown enabled to import or remove them. No files were automatically deleted.\n\n"
        + "\n\n".join(lines)
    )
    return message


def maybe_alert_blocked_imports(configuration, now_epoch, dry_run):
    delivery = configuration.get("disk_guard")
    if not delivery:
        return
    state_path = str(Path(delivery["alert_state_file"]).with_name("import-alert-epoch"))
    last_alert = read_last_active_epoch(state_path)
    if (
        last_alert is not None
        and now_epoch - last_alert < IMPORT_ALERT_INTERVAL_SECONDS
    ):
        return
    lines = blocked_download_lines(configuration)
    if not lines:
        return
    log(f"import-alert: {len(lines)} downloads need attention")
    if dry_run:
        return
    delivered = deliver_alert_message_best_effort(
        lambda: build_import_alert(lines, delivery), delivery, "blocked-download alert"
    )
    if delivered:
        write_last_active_epoch(state_path, now_epoch)
