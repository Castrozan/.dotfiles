import json
import os
import time
from pathlib import Path


def steward_workspace_directory() -> Path:
    return Path(
        os.environ.get("STEWARD_WORKSPACE_DIR", Path.home() / "clawde" / "steward")
    )


def leave_message_in_the_steward_inbox(sender: str, text: str) -> Path | None:
    steward_workspace = steward_workspace_directory()
    if not steward_workspace.is_dir():
        return None
    inbox = steward_workspace / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    sent_at = time.time()
    message = {
        "from": sender,
        "to": "steward",
        "sent_unix": int(sent_at),
        "text": text,
    }
    message_file = inbox / f"{int(sent_at * 1000)}-from-{sender}.json"
    message_file.write_text(json.dumps(message) + "\n")
    return message_file
