from command_runner import run_command_capturing_stdout
from process_table_parsers import sum_process_rss_kilobytes_by_pattern

BRAVE_RENDERER_COMMAND_MARKER = "Brave Browser Helper (Renderer)"
BROWSER_COMMAND_PATTERNS = {"brave": "Brave Browser", "chrome": "Google Chrome"}
BRAVE_EXTENSION_PROCESS_FLAG = "--extension-process"


def parse_browser_total_rss(ps_output: str) -> dict:
    return sum_process_rss_kilobytes_by_pattern(
        ps_output, BROWSER_COMMAND_PATTERNS, include_total=False
    )


def parse_brave_renderer_breakdown(ps_output: str) -> dict:
    renderer_count = 0
    renderer_rss_kilobytes = 0
    extension_renderer_count = 0
    extension_renderer_rss_kilobytes = 0
    for line in ps_output.splitlines():
        line_parts = line.strip().split(None, 1)
        if len(line_parts) != 2:
            continue
        command_text = line_parts[1]
        if BRAVE_RENDERER_COMMAND_MARKER not in command_text:
            continue
        try:
            process_rss_kilobytes = int(line_parts[0])
        except ValueError:
            continue
        renderer_count += 1
        renderer_rss_kilobytes += process_rss_kilobytes
        if BRAVE_EXTENSION_PROCESS_FLAG in command_text:
            extension_renderer_count += 1
            extension_renderer_rss_kilobytes += process_rss_kilobytes
    return {
        "renderers": renderer_count,
        "renderer_megabytes": round(renderer_rss_kilobytes / 1024, 1),
        "extension_renderers": extension_renderer_count,
        "extension_megabytes": round(extension_renderer_rss_kilobytes / 1024, 1),
    }


def parse_long_lived_brave_renderer_count(ps_output: str) -> int:
    long_lived_renderer_count = 0
    for line in ps_output.splitlines():
        line_parts = line.strip().split(None, 1)
        if len(line_parts) != 2:
            continue
        elapsed_time_text, command_text = line_parts
        if BRAVE_RENDERER_COMMAND_MARKER in command_text and "-" in elapsed_time_text:
            long_lived_renderer_count += 1
    return long_lived_renderer_count


def collect_browser_total_rss() -> list:
    ps_output = run_command_capturing_stdout(["ps", "-axo", "rss=,command="])
    rss_kilobytes_by_browser = parse_browser_total_rss(ps_output)
    return [
        {
            "metric": "browser_rss_megabytes",
            "value": round(rss_kilobytes / 1024, 1),
            "labels": {"browser": browser},
        }
        for browser, rss_kilobytes in rss_kilobytes_by_browser.items()
    ]


def collect_brave_renderer_breakdown() -> list:
    ps_output = run_command_capturing_stdout(["ps", "-axo", "rss=,command="])
    breakdown = parse_brave_renderer_breakdown(ps_output)
    return [
        {
            "metric": "brave_renderer_count",
            "value": breakdown["renderers"],
            "labels": {},
        },
        {
            "metric": "brave_renderer_megabytes",
            "value": breakdown["renderer_megabytes"],
            "labels": {},
        },
        {
            "metric": "brave_extension_renderer_count",
            "value": breakdown["extension_renderers"],
            "labels": {},
        },
        {
            "metric": "brave_extension_renderer_megabytes",
            "value": breakdown["extension_megabytes"],
            "labels": {},
        },
    ]


def collect_long_lived_brave_renderers() -> list:
    ps_output = run_command_capturing_stdout(["ps", "-axo", "etime=,command="])
    return [
        {
            "metric": "brave_long_lived_renderer_count",
            "value": parse_long_lived_brave_renderer_count(ps_output),
            "labels": {},
        }
    ]


metric_collectors = [
    ("browsers.total_rss", collect_browser_total_rss),
    ("browsers.brave_renderer_breakdown", collect_brave_renderer_breakdown),
    ("browsers.long_lived_brave_renderers", collect_long_lived_brave_renderers),
]
