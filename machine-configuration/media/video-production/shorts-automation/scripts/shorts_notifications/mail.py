import smtplib
import ssl
from email.message import EmailMessage

from .state import RECIPIENT, save, timestamp


def message_for(event):
    message = EmailMessage()
    message["From"] = RECIPIENT
    message["To"] = RECIPIENT
    message["Subject"] = f"Short publicado: {event['title']}"
    message["Message-ID"] = f"<shorts-{event['video_id']}@chise.local>"
    slot = event["run_id"]
    label = "Horário recuperado" if event["recovered"] else "Horário programado"
    message.set_content(
        f"{event['title']}\n\n{event['url']}\n\n"
        f"{label}: {slot[:10]} às {slot[11:13]}:00 (São Paulo).\n"
        "Publicação pública verificada no seu canal.\n"
    )
    return message


def connect(password_file):
    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
    try:
        server.starttls(context=ssl.create_default_context())
        server.login(RECIPIENT, password_file.read_text().strip())
    except Exception:
        server.close()
        raise
    return server


def attempt(path, record, password_file, connector=connect):
    record["attempts"] += 1
    record["attempted_at"] = timestamp()
    try:
        message = message_for(record["event"])
        server = connector(password_file)
    except (OSError, ValueError, smtplib.SMTPException) as error:
        record["error"] = type(error).__name__
        save(path, record)
        return
    try:
        dispatch(server, message, path, record)
    finally:
        server.close()


def dispatch(server, message, path, record):
    # Persist before DATA: a crash or lost acknowledgement cannot trigger an
    # automatic duplicate. Explicit SMTP rejection is safe to retry separately.
    record.update(status="delivery_uncertain", message_id=message["Message-ID"])
    save(path, record)
    try:
        server.send_message(message)
    except (
        smtplib.SMTPRecipientsRefused,
        smtplib.SMTPSenderRefused,
        smtplib.SMTPDataError,
    ) as error:
        record.update(status="pending", error=type(error).__name__)
    except (OSError, smtplib.SMTPException) as error:
        record["error"] = type(error).__name__
    else:
        record.update(status="sent", sent_at=timestamp())
        record.pop("error", None)
    save(path, record)
