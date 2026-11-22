import argparse
import dataclasses
import json
import math
import os
from datetime import datetime

import switch_moments
import switch_records
import switch_report
import transcript_log
from switch_moments import Switch

HISTORY_FILE = "switch-latency.jsonl"
KEPT_SWITCHES = 1000


def logged_lines(wake_log):
    for path in sorted(wake_log.parent.glob(f"{wake_log.name}*")):
        with path.open(encoding="utf-8", errors="backslashreplace") as log:
            yield from log


def remembered(history):
    if not history.exists():
        return []
    return [Switch(**json.loads(line)) for line in history.read_text().splitlines()]


def merged(history, fresh):
    by_moment = {switch.switched_at: switch for switch in history}
    by_moment |= {switch.switched_at: switch for switch in fresh}
    ordered = sorted(by_moment.values(), key=lambda switch: switch.switched_at)
    return ordered[-KEPT_SWITCHES:]


def keep(history, switches):
    history.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    staged = history.with_name(f"{history.name}.partial")
    descriptor = os.open(staged, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as output:
        output.writelines(
            json.dumps(dataclasses.asdict(switch)) + "\n" for switch in switches
        )
    os.replace(staged, history)


def recorded_switches(wake_log):
    history = wake_log.with_name(HISTORY_FILE)
    fresh = switch_moments.switches_in(
        switch_records.logged_records(logged_lines(wake_log))
    )
    switches = merged(remembered(history), fresh)
    keep(history, switches)
    return switches


def moment(text):
    return datetime.fromisoformat(text).astimezone().timestamp()


def start_of_today():
    now = datetime.now().astimezone()
    return now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()


def window_title(since, until):
    end = "now" if until == math.inf else f"{datetime.fromtimestamp(until):%F %R}"
    return f"Switch round trips from {datetime.fromtimestamp(since):%F %R} to {end}\n"


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="avatar-switch-latency",
        description="Time every stage from the end of the user's speech naming "
        "another agent to the first audio of that agent's reply.",
    )
    parser.add_argument("--since", type=moment, default=start_of_today())
    parser.add_argument("--until", type=moment, default=math.inf)
    parser.add_argument(
        "--record",
        action="store_true",
        help="only keep the switches in the wake log in the lasting history",
    )
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    switches = recorded_switches(transcript_log.wake_log_path())
    if arguments.record:
        return
    shown = [
        switch
        for switch in switches
        if arguments.since <= switch.switched_at < arguments.until
    ]
    print(window_title(arguments.since, arguments.until))
    print(switch_report.report(shown))


if __name__ == "__main__":
    main()
