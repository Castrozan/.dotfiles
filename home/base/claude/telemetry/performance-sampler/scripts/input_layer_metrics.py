import json
from pathlib import Path

from command_runner import run_command_capturing_stdout

KARABINER_HEALTH_FILE_PATH = Path("/tmp/karabiner-health.json")
INPUT_DAEMON_NAMES = ["workspace-window-switcher-daemon", "application-launcher-daemon"]
KARABINER_HEALTH_FIELD_TO_METRIC = {
    "kick_count_total": "karabiner_kick_count_total",
    "karabiner_cli_ipc_probe_failure_count_total": "karabiner_ipc_probe_failure_count_total",
    "karabiner_grabbed_keyboard_device_count": "karabiner_grabbed_keyboard_device_count",
}


def parse_elapsed_time_to_seconds(elapsed_time_text: str) -> int:
    day_count = 0
    remainder = elapsed_time_text.strip()
    if "-" in remainder:
        day_text, remainder = remainder.split("-", 1)
        day_count = int(day_text)
    time_components = [int(component) for component in remainder.split(":")]
    while len(time_components) < 3:
        time_components.insert(0, 0)
    hours, minutes, seconds = time_components
    return ((day_count * 24 + hours) * 60 + minutes) * 60 + seconds


def collect_karabiner_health() -> list:
    if not KARABINER_HEALTH_FILE_PATH.exists():
        return []
    karabiner_health = json.loads(
        KARABINER_HEALTH_FILE_PATH.read_text(encoding="utf-8")
    )
    karabiner_records = []
    for field_name, metric_name in KARABINER_HEALTH_FIELD_TO_METRIC.items():
        if field_name in karabiner_health:
            karabiner_records.append(
                {
                    "metric": metric_name,
                    "value": karabiner_health[field_name],
                    "labels": {},
                }
            )
    return karabiner_records


def collect_input_daemon_uptime() -> list:
    uptime_records = []
    for daemon_name in INPUT_DAEMON_NAMES:
        matching_pids = run_command_capturing_stdout(
            ["pgrep", "-f", daemon_name]
        ).split()
        if not matching_pids:
            continue
        elapsed_time_text = run_command_capturing_stdout(
            ["ps", "-o", "etime=", "-p", matching_pids[0]]
        ).strip()
        if not elapsed_time_text:
            continue
        uptime_records.append(
            {
                "metric": "input_daemon_uptime_seconds",
                "value": parse_elapsed_time_to_seconds(elapsed_time_text),
                "labels": {"daemon": daemon_name},
            }
        )
    return uptime_records


metric_collectors = [
    ("input_layer.karabiner_health", collect_karabiner_health),
    ("input_layer.input_daemon_uptime", collect_input_daemon_uptime),
]
