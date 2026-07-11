from command_runner import run_command_capturing_stdout
from process_table_parsers import command_first_token_basename, sum_process_cpu_percent


def sum_process_cpu_and_rss_by_executable_name(
    ps_output: str, executable_base_name: str
) -> dict:
    total_cpu_percent = 0.0
    total_rss_kilobytes = 0
    for line in ps_output.splitlines():
        line_parts = line.strip().split(None, 2)
        if len(line_parts) < 3:
            continue
        try:
            process_cpu_percent = float(line_parts[0])
            process_rss_kilobytes = int(line_parts[1])
        except ValueError:
            continue
        if line_parts[2].split("/")[-1] == executable_base_name:
            total_cpu_percent += process_cpu_percent
            total_rss_kilobytes += process_rss_kilobytes
    return {
        "cpu_percent": round(total_cpu_percent, 1),
        "rss_megabytes": round(total_rss_kilobytes / 1024, 1),
    }


def collect_wezterm_gui_process() -> list:
    ps_output = run_command_capturing_stdout(["ps", "-Ao", "pcpu=,rss=,comm="])
    statistics = sum_process_cpu_and_rss_by_executable_name(ps_output, "wezterm-gui")
    return [
        {
            "metric": "wezterm_gui_cpu_percent",
            "value": statistics["cpu_percent"],
            "labels": {},
        },
        {
            "metric": "wezterm_gui_rss_megabytes",
            "value": statistics["rss_megabytes"],
            "labels": {},
        },
    ]


def collect_window_server_cpu() -> list:
    ps_output = run_command_capturing_stdout(["ps", "-Ao", "pcpu=,comm="])
    window_server_cpu_percent = sum_process_cpu_percent(
        ps_output,
        lambda command_text: command_first_token_basename(command_text)
        == "WindowServer",
    )
    return [
        {
            "metric": "window_server_cpu_percent",
            "value": window_server_cpu_percent,
            "labels": {},
        }
    ]


metric_collectors = [
    ("terminal.wezterm_gui", collect_wezterm_gui_process),
    ("terminal.window_server_cpu", collect_window_server_cpu),
]
