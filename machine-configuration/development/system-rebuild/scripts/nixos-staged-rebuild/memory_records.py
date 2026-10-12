import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class RebuildRun:
    action: str
    host: str
    started_at: str
    exit_status: int


def append_record(record):
    destination = os.environ.get("REBUILD_MEMORY_RECORDS")
    if not destination:
        return
    try:
        with Path(destination).open("a") as output:
            output.write(json.dumps(record) + "\n")
    except OSError as error:
        print(
            f"warning: cannot record rebuild memory metrics: {error}", file=sys.stderr
        )


def component_details(records):
    return {record["component"]: record for record in records if "component" in record}


def measurement_records(records):
    details = component_details(records)
    measurements = [dict(record) for record in records if "phase" in record]
    for measurement in measurements:
        measurement.update(details.get(measurement["phase"], {}))
        measurement["peak_rss_mib"] = measurement["peak_rss_kib"] / 1024
    return measurements


def source_context(records):
    return next(
        (record["sources"] for record in reversed(records) if "sources" in record), {}
    )


def create_report(records, rebuild_run):
    measurements = measurement_records(records)
    return {
        "host": rebuild_run.host,
        "action": rebuild_run.action,
        "started_at": rebuild_run.started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "exit_status": rebuild_run.exit_status,
        "sources": source_context(records),
        "scope": "Peak RSS of command process trees; shared Nix daemon workers are outside these measurements. Isolated component peaks overlap and must not be added.",
        "phases": [
            value
            for value in measurements
            if not value["phase"].startswith("component_")
        ],
        "components": [
            value for value in measurements if value["phase"].startswith("component_")
        ],
    }


def write_report(destination, report):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=destination.parent, delete=False
    ) as output:
        temporary = Path(output.name)
        json.dump(report, output, indent=2)
        output.write("\n")
    try:
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def publish_report(records_path, directory, rebuild_run):
    if rebuild_run.exit_status == 99:
        return
    records = [json.loads(line) for line in Path(records_path).read_text().splitlines()]
    if not records:
        return
    report = create_report(records, rebuild_run)
    destination = Path(directory) / "latest.json"
    write_report(destination, report)
    print(f"Rebuild memory metrics: {destination}")
    if report["components"]:
        destination = Path(directory) / "latest-components.json"
        write_report(destination, report)
        print(f"Component memory metrics: {destination}")
    else:
        print("Run rebuild --measure-memory to refresh isolated component peaks.")
