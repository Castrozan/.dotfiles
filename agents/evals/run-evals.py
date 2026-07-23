#!/usr/bin/env python3

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_evals_ab import run_instruction_loading_experiment  # noqa: E402
from run_evals_baseline import (  # noqa: F401, E402
    BASELINE_PATH,
    MAXIMUM_REGRESSION_DROP,
    MINIMUM_PASS_RATE_COMPLIANCE,
    MINIMUM_PASS_RATE_OVERALL,
    build_baseline_from_results,
    check_baseline_for_regression,
    get_current_git_commit,
    save_baseline,
    write_baseline,
)
from run_evals_claude_cli import run_claude_cli  # noqa: F401, E402
from run_evals_config_loader import (  # noqa: F401, E402
    discover_skill_adjacent_eval_files,
    load_config,
    load_config_from_dir,
    load_skill_body_from_path,
    resolve_system_prompt_for_test,
)
from run_evals_reporting import (  # noqa: F401, E402
    list_categories,
    print_ab_summary,
    print_epoch_summary,
    print_results,
)
from run_evals_sampling import (  # noqa: E402
    aggregate_repeated_runs,
    build_epoch_enriched_baseline,
)
from run_evals_test_runner import (  # noqa: F401, E402
    DEFAULT_PARALLEL_WORKERS,
    TestResult,
    check_assertions,
    run_test,
    run_tests,
)
from run_evals_worktree_and_environment import (  # noqa: F401, E402
    EVAL_WORKING_DIRECTORY,
    REPO_ROOT,
    build_filtered_environment,
    temporary_eval_worktree,
)


def main():
    parser = argparse.ArgumentParser(
        description="Run agent evaluations (Claude Max/CLI)"
    )
    parser.add_argument("--smoke", action="store_true", help="Run smoke test only")
    parser.add_argument("--category", help="Run tests in specific category")
    parser.add_argument("--test", help="Run specific test by name")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available categories and tests",
    )
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Run all tests and save results as baseline",
    )
    parser.add_argument(
        "--check-baseline",
        action="store_true",
        help="Check committed baseline for regression (no claude calls)",
    )
    parser.add_argument("--config", default=Path(__file__).parent / "config")
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=f"Max parallel workers (default: {DEFAULT_PARALLEL_WORKERS})",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=1,
        help="Repeat the suite N times to surface flakiness (pass@k and CIs)",
    )
    parser.add_argument(
        "--ab",
        action="store_true",
        help="Paired A/B: same tests with vs without the instruction surface",
    )
    args = parser.parse_args()

    if args.check_baseline:
        passed = check_baseline_for_regression()
        sys.exit(0 if passed else 1)

    config = load_config(Path(args.config))

    if args.list:
        list_categories(config)
        sys.exit(0)

    if not args.dry_run:
        result = subprocess.run(["which", "claude"], capture_output=True)
        if result.returncode != 0:
            print("Error: claude CLI not found")
            print("Run 'rebuild' to install Claude Code")
            sys.exit(1)

    print("Running agent evaluations (Claude Max - no API cost)...")
    if args.dry_run:
        print("   (dry run - no claude calls)")

    if args.ab:
        with temporary_eval_worktree():
            comparison = run_instruction_loading_experiment(
                config,
                category=args.category,
                max_workers_override=args.workers,
            )
        print_ab_summary(comparison)
        sys.exit(0)

    if args.epochs > 1:
        with temporary_eval_worktree():
            results_per_epoch = []
            for epoch_index in range(args.epochs):
                print(f"\n--- epoch {epoch_index + 1}/{args.epochs} ---")
                results_per_epoch.append(
                    run_tests(
                        config,
                        category=args.category,
                        test_name=args.test,
                        dry_run=args.dry_run,
                        smoke_only=args.smoke,
                        max_workers_override=args.workers,
                    )
                )
        per_test = aggregate_repeated_runs(results_per_epoch)
        no_hard_failures = print_epoch_summary(per_test, args.epochs)
        if args.save_baseline:
            write_baseline(
                build_epoch_enriched_baseline(
                    per_test,
                    args.epochs,
                    get_current_git_commit(),
                    datetime.now(timezone.utc).isoformat(),
                )
            )
        sys.exit(0 if no_hard_failures else 1)

    with temporary_eval_worktree():
        results = run_tests(
            config,
            category=args.category,
            test_name=args.test,
            dry_run=args.dry_run,
            smoke_only=args.smoke,
            max_workers_override=args.workers,
        )

    all_passed = print_results(results)

    if args.save_baseline:
        save_baseline(results)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
