from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

LEDGER_FILE_NAME = "silent-background-commands.jsonl"


def default_ledger_path():
    state_home = os.environ.get("XDG_STATE_HOME") or os.path.expanduser(
        "~/.local/state"
    )
    return Path(state_home) / "background-wait-tracker" / LEDGER_FILE_NAME


def load_records_by_id(ledger_path):
    if not Path(ledger_path).is_file():
        return {}
    records_by_id = {}
    for ledger_line in Path(ledger_path).read_text().splitlines():
        if ledger_line.strip():
            record = json.loads(ledger_line)
            records_by_id[record["id"]] = record
    return records_by_id


def save_records(ledger_path, records_by_id):
    ledger_directory = Path(ledger_path).parent
    ledger_directory.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", dir=ledger_directory, delete=False, suffix=".tmp"
    ) as replacement_file:
        for record in sorted(
            records_by_id.values(), key=lambda record: record["launched_at"]
        ):
            replacement_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    os.replace(replacement_file.name, ledger_path)


def record_silent_commands(ledger_path, silent_command_records):
    records_by_id = load_records_by_id(ledger_path)
    newly_recorded_ids = []
    for record in silent_command_records:
        known_record = records_by_id.get(record["id"])
        if known_record is None:
            newly_recorded_ids.append(record["id"])
        else:
            record = {**record, "dismissed_reason": known_record["dismissed_reason"]}
        records_by_id[record["id"]] = record
    save_records(ledger_path, records_by_id)
    return newly_recorded_ids


def dismiss_record(ledger_path, record_id, reason):
    records_by_id = load_records_by_id(ledger_path)
    if record_id not in records_by_id:
        raise KeyError(record_id)
    records_by_id[record_id]["dismissed_reason"] = reason
    save_records(ledger_path, records_by_id)
