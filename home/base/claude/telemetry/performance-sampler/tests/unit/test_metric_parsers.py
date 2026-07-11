import sys
from pathlib import Path

PERFORMANCE_SAMPLER_SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(PERFORMANCE_SAMPLER_SCRIPTS_DIRECTORY))

import process_table_parsers
import system_health_metrics


def test_parse_swap_usage_megabytes_extracts_total_used_free():
    swapusage_output = (
        "total = 13312.00M  used = 11688.00M  free = 1624.00M  (encrypted)"
    )
    parsed = system_health_metrics.parse_swap_usage_megabytes(swapusage_output)
    assert parsed == {"total": 13312.0, "used": 11688.0, "free": 1624.0}


def test_parse_load_average_returns_three_windows():
    assert system_health_metrics.parse_load_average("{ 3.56 2.79 3.07 }") == [
        3.56,
        2.79,
        3.07,
    ]


def test_parse_vm_stat_interval_deltas_reads_last_row_by_column_name():
    vm_stat_output = "\n".join(
        [
            "Mach Virtual Memory Statistics: (page size of 16384 bytes)",
            "free comprs dcomprs swapins swapouts",
            "100 5000 4000 10 20",
            "110 500 400 1 2",
        ]
    )
    deltas = system_health_metrics.parse_vm_stat_interval_deltas(
        vm_stat_output, ["comprs", "dcomprs", "swapins", "swapouts"]
    )
    assert deltas == {"comprs": 500, "dcomprs": 400, "swapins": 1, "swapouts": 2}


def test_sum_process_rss_kilobytes_by_pattern_buckets_and_totals():
    ps_output = "\n".join(
        [
            " 5000 /Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            " 2000 /nix/store/abc/bin/claude --resume",
            " 100 herdr",
        ]
    )
    parsed = process_table_parsers.sum_process_rss_kilobytes_by_pattern(
        ps_output,
        system_health_metrics.MEMORY_FAMILY_COMMAND_PATTERNS,
        include_total=True,
    )
    assert parsed["brave"] == 5000
    assert parsed["claude"] == 2000
    assert parsed["herdr"] == 100
    assert parsed["total"] == 7100


def test_sum_process_cpu_percent_applies_predicate():
    ps_output = "\n".join(
        [
            "12.5 /System/Library/.../Support/mds_stores",
            "3.0 /System/Library/.../Support/mds",
            "9.9 /usr/bin/other",
        ]
    )
    total = process_table_parsers.sum_process_cpu_percent(
        ps_output,
        lambda command_text: process_table_parsers.command_first_token_basename(
            command_text
        )
        in {"mds", "mds_stores"},
    )
    assert total == 15.5
