import shutil
import subprocess
import sys

from benchmark_core import DOTFILES_DIRECTORY

DESKTOP_BENCHMARK_COMMAND = "benchmark-desktop"
SHELL_BENCHMARK_COMMAND = "benchmark-shell"
REBUILD_BENCHMARK_COMMAND = "benchmark-rebuild"
THRESHOLD_TEST_RUNNER = "bats"

THRESHOLD_TEST_ROOT = DOTFILES_DIRECTORY / "machine-configuration"
THRESHOLD_TEST_FILE_NAME = "perf-runtime.bats"

DEFAULT_ITERATIONS = "5"
COMMAND_NOT_FOUND_STATUS = 127


def run_delegated_command(arguments: list[str]) -> int:
    program = arguments[0]
    if shutil.which(program) is None:
        print(
            f"{program} is not available on this machine, so dotfiles-perf "
            "cannot run it. The testing capability packages it only where its "
            "platform supports it.",
            file=sys.stderr,
        )
        return COMMAND_NOT_FOUND_STATUS
    return subprocess.run(arguments).returncode


def find_threshold_test_files() -> list[str]:
    return sorted(
        str(path) for path in THRESHOLD_TEST_ROOT.rglob(THRESHOLD_TEST_FILE_NAME)
    )


def run_desktop_benchmarks(arguments: list[str]) -> int:
    return run_delegated_command([DESKTOP_BENCHMARK_COMMAND, *arguments])


def compare_latest_run(arguments: list[str]) -> int:
    return run_delegated_command([DESKTOP_BENCHMARK_COMMAND, "--compare-latest"])


def validate_committed_baseline(arguments: list[str]) -> int:
    return run_delegated_command([DESKTOP_BENCHMARK_COMMAND, "--check-baseline"])


def save_new_baseline(arguments: list[str]) -> int:
    return run_delegated_command([DESKTOP_BENCHMARK_COMMAND, "--save-baseline"])


def print_benchmark_history(arguments: list[str]) -> int:
    return run_delegated_command([DESKTOP_BENCHMARK_COMMAND, "report"])


def run_shell_benchmarks(arguments: list[str]) -> int:
    return run_delegated_command([SHELL_BENCHMARK_COMMAND, *arguments])


def run_rebuild_benchmarks(arguments: list[str]) -> int:
    return run_delegated_command([REBUILD_BENCHMARK_COMMAND, *arguments])


def run_threshold_tests(arguments: list[str]) -> int:
    test_files = find_threshold_test_files()
    if not test_files:
        print(
            f"No {THRESHOLD_TEST_FILE_NAME} files under {THRESHOLD_TEST_ROOT}.",
            file=sys.stderr,
        )
        return 1
    return run_delegated_command([THRESHOLD_TEST_RUNNER, *test_files])


def run_full_suite(arguments: list[str]) -> int:
    iterations = arguments[0] if arguments else DEFAULT_ITERATIONS

    print("=== Performance Suite ===")
    print()
    print("--- Benchmarks ---")
    measurement_status = run_desktop_benchmarks([iterations])
    if measurement_status != 0:
        return measurement_status

    print()
    print("--- Regression Check ---")
    comparison_status = compare_latest_run([])
    if comparison_status != 0:
        return comparison_status

    print()
    print("--- Threshold Tests ---")
    return run_threshold_tests([])


COMMANDS = {
    "run": run_desktop_benchmarks,
    "check": compare_latest_run,
    "validate": validate_committed_baseline,
    "test": run_threshold_tests,
    "baseline": save_new_baseline,
    "report": print_benchmark_history,
    "all": run_full_suite,
    "shell": run_shell_benchmarks,
    "rebuild": run_rebuild_benchmarks,
}


def print_usage() -> None:
    print("Usage: dotfiles-perf <command> [args]")
    print()
    print("Commands:")
    print("  run [iters] [component]  Run desktop benchmarks (default: 5 iterations)")
    print("  check                    Compare the latest run against the baseline")
    print("  validate                 Validate the committed baseline")
    print("  test                     Run perf threshold tests (bats)")
    print("  baseline                 Measure and save new baseline")
    print("  report                   Show benchmark history")
    print("  all [iters]              Run benchmarks + check + threshold tests")
    print("  shell [iters] [shell]    Run shell startup benchmark")
    print("  rebuild [command]        Run rebuild benchmark")
    print()
    print("Examples:")
    print("  dotfiles-perf run              # benchmark all, 5 iterations")
    print("  dotfiles-perf run 10 tmux      # benchmark tmux only, 10 iterations")
    print("  dotfiles-perf check            # regression check against baseline")
    print("  dotfiles-perf validate         # tracked baseline schema and freshness")
    print("  dotfiles-perf test             # pass/fail threshold tests")
    print("  dotfiles-perf all              # full perf suite")
    print("  dotfiles-perf baseline         # save new baseline")


def main() -> None:
    argv = sys.argv[1:]
    command = argv[0] if argv else ""

    if command in ("", "-h", "--help"):
        print_usage()
        return

    handler = COMMANDS.get(command)
    if handler is None:
        print(f"Unknown command: {command}", file=sys.stderr)
        print_usage()
        raise SystemExit(1)

    raise SystemExit(handler(argv[1:]))


if __name__ == "__main__":
    main()
