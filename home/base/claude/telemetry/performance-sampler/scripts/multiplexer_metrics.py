import json
import os
import time

from command_runner import resolve_executable_path, run_command_capturing_stdout


def find_herdr_server_pid(ps_output: str):
    for line in ps_output.splitlines():
        line_parts = line.strip().split(None, 1)
        if len(line_parts) != 2:
            continue
        process_pid, command_text = line_parts
        command_tokens = command_text.split()
        if not command_tokens:
            continue
        executable_base_name = command_tokens[0].split("/")[-1]
        if executable_base_name == "herdr" and command_tokens[1:2] == ["server"]:
            return process_pid
    return None


def parse_herdr_topology(workspace_list_json: str) -> dict:
    workspace_list = json.loads(workspace_list_json)["result"]["workspaces"]
    return {
        "workspaces": len(workspace_list),
        "tabs": sum(workspace.get("tab_count", 0) for workspace in workspace_list),
        "panes": sum(workspace.get("pane_count", 0) for workspace in workspace_list),
    }


def collect_herdr_server_process() -> list:
    ps_output = run_command_capturing_stdout(["ps", "-axo", "pid=,command="])
    herdr_server_pid = find_herdr_server_pid(ps_output)
    if herdr_server_pid is None:
        return []
    process_statistics = run_command_capturing_stdout(
        ["ps", "-p", herdr_server_pid, "-o", "pcpu=,rss="]
    ).split()
    if len(process_statistics) < 2:
        return []
    return [
        {
            "metric": "herdr_server_cpu_percent",
            "value": float(process_statistics[0]),
            "labels": {},
        },
        {
            "metric": "herdr_server_rss_megabytes",
            "value": round(int(process_statistics[1]) / 1024, 1),
            "labels": {},
        },
    ]


def collect_herdr_topology() -> list:
    if resolve_executable_path("herdr") is None:
        return []
    workspace_list_output = run_command_capturing_stdout(["herdr", "workspace", "list"])
    topology = parse_herdr_topology(workspace_list_output)
    return [
        {"metric": "herdr_workspaces", "value": topology["workspaces"], "labels": {}},
        {"metric": "herdr_tabs", "value": topology["tabs"], "labels": {}},
        {"metric": "herdr_panes", "value": topology["panes"], "labels": {}},
    ]


def collect_herdr_control_plane_round_trip() -> list:
    if resolve_executable_path("herdr") is None:
        return []
    started_at = time.perf_counter()
    run_command_capturing_stdout(["herdr", "api", "snapshot"])
    round_trip_milliseconds = round((time.perf_counter() - started_at) * 1000, 1)
    return [
        {
            "metric": "herdr_control_plane_rtt_milliseconds",
            "value": round_trip_milliseconds,
            "labels": {},
        }
    ]


def collect_herdr_binary_staleness() -> list:
    ps_output = run_command_capturing_stdout(["ps", "-axo", "pid=,command="])
    herdr_server_pid = find_herdr_server_pid(ps_output)
    installed_herdr_path = resolve_executable_path("herdr")
    if herdr_server_pid is None or installed_herdr_path is None:
        return []
    installed_real_path = os.path.realpath(installed_herdr_path)
    lsof_output = run_command_capturing_stdout(["lsof", "-p", herdr_server_pid])
    running_text_path = None
    for line in lsof_output.splitlines():
        lsof_fields = line.split()
        if len(lsof_fields) >= 5 and lsof_fields[3] == "txt":
            running_text_path = lsof_fields[-1]
            break
    if running_text_path is None:
        return []
    is_stale = os.path.realpath(running_text_path) != installed_real_path
    return [
        {"metric": "herdr_binary_stale", "value": 1 if is_stale else 0, "labels": {}}
    ]


def collect_opencode_process() -> list:
    ps_output = run_command_capturing_stdout(["ps", "-axo", "rss=,comm="])
    aggregate_rss_kilobytes = 0
    found_opencode_process = False
    for line in ps_output.splitlines():
        line_parts = line.strip().split(None, 1)
        if len(line_parts) != 2:
            continue
        if line_parts[1].split("/")[-1] == "opencode":
            try:
                aggregate_rss_kilobytes += int(line_parts[0])
                found_opencode_process = True
            except ValueError:
                continue
    if not found_opencode_process:
        return []
    return [
        {
            "metric": "opencode_rss_megabytes",
            "value": round(aggregate_rss_kilobytes / 1024, 1),
            "labels": {},
        }
    ]


metric_collectors = [
    ("multiplexer.herdr_server_process", collect_herdr_server_process),
    ("multiplexer.herdr_topology", collect_herdr_topology),
    (
        "multiplexer.herdr_control_plane_round_trip",
        collect_herdr_control_plane_round_trip,
    ),
    ("multiplexer.herdr_binary_staleness", collect_herdr_binary_staleness),
    ("multiplexer.opencode_process", collect_opencode_process),
]
