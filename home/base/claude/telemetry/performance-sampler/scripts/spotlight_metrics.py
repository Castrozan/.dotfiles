from command_runner import run_command_capturing_stdout
from process_table_parsers import command_first_token_basename, sum_process_cpu_percent

SPOTLIGHT_PROCESS_EXECUTABLE_NAMES = {"mds", "mds_stores"}


def collect_spotlight_cpu() -> list:
    ps_output = run_command_capturing_stdout(["ps", "-Ao", "pcpu=,comm="])
    spotlight_cpu_percent = sum_process_cpu_percent(
        ps_output,
        lambda command_text: command_first_token_basename(command_text)
        in SPOTLIGHT_PROCESS_EXECUTABLE_NAMES,
    )
    return [
        {
            "metric": "spotlight_cpu_percent",
            "value": spotlight_cpu_percent,
            "labels": {},
        }
    ]


metric_collectors = [
    ("spotlight.cpu", collect_spotlight_cpu),
]
