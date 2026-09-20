import pathlib

import benchmark_core
import benchmark_result_rows
import desktop_benchmarks.measurement

RESULTS_FILE_NAME = "desktop-times.csv"


CSV_HEADER = "timestamp,component,avg_ms,min_ms,max_ms,iterations"


RECENT_RESULT_ROW_LIMIT = 30


def get_results_file_path() -> pathlib.Path:
    return benchmark_core.RESULTS_DIRECTORY / RESULTS_FILE_NAME


def record_result(
    results_file: pathlib.Path,
    name: str,
    avg_ms: float,
    min_ms: float,
    max_ms: float,
    iterations: int,
) -> None:
    benchmark_core.append_result_row(
        results_file,
        [
            name,
            f"{avg_ms:.1f}",
            f"{min_ms:.1f}",
            f"{max_ms:.1f}",
            str(iterations),
        ],
    )


def format_ms(ms: float) -> str:
    if ms < 1000:
        return f"{ms:.0f}ms"
    return f"{ms / 1000:.2f}s"


def run_benchmarks(
    benchmarks: list[tuple[str, object]],
    iterations: int,
    results_file: pathlib.Path,
) -> list[dict]:
    results = []
    for name, fn in benchmarks:
        print(f"  {name} ({iterations}x) ", end="", flush=True)
        result = desktop_benchmarks.measurement.measure_iterations(name, fn, iterations)
        results.append(result)

        if result["error"]:
            print("    FAILED (all iterations errored)")
        else:
            print(
                f"    avg={format_ms(result['avg'])}  "
                f"min={format_ms(result['min'])}  "
                f"max={format_ms(result['max'])}"
            )
            record_result(
                results_file,
                name,
                result["avg"],
                result["min"],
                result["max"],
                len(result["times"]),
            )

    return results


def print_summary(results: list[dict]) -> None:
    print()
    print("=" * 62)
    print(f"{'Component':<22} {'Avg':>8} {'Min':>8} {'Max':>8}")
    print("-" * 62)
    for r in results:
        if r["error"]:
            print(f"{r['name']:<22} {'FAILED':>8}")
        else:
            print(
                f"{r['name']:<22} "
                f"{format_ms(r['avg']):>8} "
                f"{format_ms(r['min']):>8} "
                f"{format_ms(r['max']):>8}"
            )
    print("=" * 62)


def print_report(results_file: pathlib.Path) -> None:
    lines = results_file.read_text().splitlines() if results_file.exists() else []
    if len(lines) <= 1:
        print("No benchmark results found.")
        return

    print("=== Recent Desktop Benchmark Results ===")
    for row in benchmark_result_rows.recent_result_table_lines(
        lines, RECENT_RESULT_ROW_LIMIT
    ):
        print(row)

    print()
    _print_averages(lines[1:])


def _print_averages(data_lines: list[str]) -> None:
    print("=== Averages by Component ===")
    averages = benchmark_result_rows.aggregate_values_by_key(data_lines, (1,), 2)
    for name, aggregate in sorted(averages.items()):
        print(
            f"  {name}: {format_ms(aggregate.total / aggregate.count)} avg "
            f"({aggregate.count} runs)"
        )
