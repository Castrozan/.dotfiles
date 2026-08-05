from command_runner import run_command_capturing_stdout
from process_table_parsers import sum_process_rss_kilobytes_by_pattern

MEMORY_FAMILY_COMMAND_PATTERNS = {
    "brave": "Brave Browser",
    "chrome": "Google Chrome",
    "claude": "/bin/claude",
    "chrome_devtools_mcp": "chrome-devtools-mcp",
    "node": "/node",
    "opencode": "opencode",
    "java": "/java",
    "herdr": "herdr",
    "wezterm": "wezterm",
}

VM_STAT_CHURN_WINDOW_SECONDS = 5

VM_STAT_CHURN_COLUMNS = {
    "comprs": "compressions_per_second",
    "dcomprs": "decompressions_per_second",
    "swapins": "swapins_per_second",
    "swapouts": "swapouts_per_second",
}


def parse_swap_usage_megabytes(swapusage_output: str) -> dict:
    swap_megabytes_by_kind = {}
    for keyword in ("total", "used", "free"):
        marker = keyword + " ="
        marker_index = swapusage_output.find(marker)
        if marker_index == -1:
            continue
        remainder = swapusage_output[marker_index + len(marker) :].strip()
        number_text = remainder.split("M", 1)[0].strip()
        try:
            swap_megabytes_by_kind[keyword] = float(number_text)
        except ValueError:
            continue
    return swap_megabytes_by_kind


def parse_load_average(loadavg_output: str) -> list:
    cleaned_tokens = loadavg_output.replace("{", "").replace("}", "").split()
    return [float(token) for token in cleaned_tokens[:3]]


def parse_vm_stat_interval_deltas(vm_stat_output: str, wanted_column_names) -> dict:
    non_empty_lines = [line for line in vm_stat_output.splitlines() if line.strip()]
    header_line_index = None
    for line_index, line in enumerate(non_empty_lines):
        if "comprs" in line.split():
            header_line_index = line_index
            break
    if header_line_index is None:
        return {}
    header_tokens = non_empty_lines[header_line_index].split()
    data_rows = [line.split() for line in non_empty_lines[header_line_index + 1 :]]
    aligned_data_rows = [row for row in data_rows if len(row) == len(header_tokens)]
    if len(aligned_data_rows) < 2:
        return {}
    interval_delta_row = aligned_data_rows[-1]
    interval_deltas = {}
    for column_name in wanted_column_names:
        if column_name not in header_tokens:
            continue
        column_index = header_tokens.index(column_name)
        try:
            interval_deltas[column_name] = int(interval_delta_row[column_index])
        except ValueError:
            continue
    return interval_deltas


def collect_memory_pressure_level() -> list:
    pressure_output = run_command_capturing_stdout(
        ["sysctl", "-n", "kern.memorystatus_vm_pressure_level"]
    ).strip()
    return [
        {"metric": "memory_pressure_level", "value": int(pressure_output), "labels": {}}
    ]


def collect_swap_usage() -> list:
    swapusage_output = run_command_capturing_stdout(["sysctl", "-n", "vm.swapusage"])
    swap_megabytes_by_kind = parse_swap_usage_megabytes(swapusage_output)
    return [
        {"metric": "swap_megabytes", "value": megabytes, "labels": {"kind": kind}}
        for kind, megabytes in swap_megabytes_by_kind.items()
    ]


def collect_load_average() -> list:
    loadavg_output = run_command_capturing_stdout(["sysctl", "-n", "vm.loadavg"])
    load_averages = parse_load_average(loadavg_output)
    window_labels = ["1m", "5m", "15m"]
    return [
        {"metric": "load_average", "value": load_average, "labels": {"window": window}}
        for window, load_average in zip(window_labels, load_averages)
    ]


def collect_compressor_churn() -> list:
    vm_stat_output = run_command_capturing_stdout(
        ["vm_stat", "-c", "2", str(VM_STAT_CHURN_WINDOW_SECONDS)],
        timeout_seconds=VM_STAT_CHURN_WINDOW_SECONDS + 15.0,
    )
    interval_deltas = parse_vm_stat_interval_deltas(
        vm_stat_output, VM_STAT_CHURN_COLUMNS.keys()
    )
    churn_records = []
    for column_name, metric_name in VM_STAT_CHURN_COLUMNS.items():
        if column_name not in interval_deltas:
            continue
        per_second_value = round(
            interval_deltas[column_name] / VM_STAT_CHURN_WINDOW_SECONDS, 1
        )
        churn_records.append(
            {"metric": metric_name, "value": per_second_value, "labels": {}}
        )
    return churn_records


def collect_per_family_memory() -> list:
    ps_output = run_command_capturing_stdout(["ps", "-axo", "rss=,command="])
    family_rss_kilobytes = sum_process_rss_kilobytes_by_pattern(
        ps_output, MEMORY_FAMILY_COMMAND_PATTERNS, include_total=True
    )
    return [
        {
            "metric": "family_rss_megabytes",
            "value": round(rss_kilobytes / 1024, 1),
            "labels": {"family": family},
        }
        for family, rss_kilobytes in family_rss_kilobytes.items()
    ]


def collect_thermal_warning_state() -> list:
    thermal_output = run_command_capturing_stdout(["pmset", "-g", "therm"])
    is_clean = (
        1 if "No thermal warning level has been recorded" in thermal_output else 0
    )
    return [{"metric": "thermal_warning_clean", "value": is_clean, "labels": {}}]


metric_collectors = [
    ("system_health.memory_pressure_level", collect_memory_pressure_level),
    ("system_health.swap_usage", collect_swap_usage),
    ("system_health.compressor_churn", collect_compressor_churn),
    ("system_health.per_family_memory", collect_per_family_memory),
    ("system_health.load_average", collect_load_average),
    ("system_health.thermal_warning_state", collect_thermal_warning_state),
]
