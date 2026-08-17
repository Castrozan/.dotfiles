#!/usr/bin/env python3

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_evals_ab import run_instruction_loading_experiment  # noqa: E402
from run_evals_ab_record import save_ab_profile  # noqa: E402
from run_evals_arguments import parse_arguments  # noqa: E402
from run_evals_baseline import check_baseline_for_regression  # noqa: E402
from run_evals_baseline_record import (  # noqa: F401, E402
    get_current_git_commit,
    merge_baseline_snapshot,
    save_baseline,
    write_baseline,
)
from run_evals_baseline_thresholds import (  # noqa: F401, E402
    MAXIMUM_REGRESSION_DROP,
    MINIMUM_PASS_RATE_COMPLIANCE,
    MINIMUM_PASS_RATE_OVERALL,
)
from run_evals_claude_cli import run_claude_cli  # noqa: E402
from run_evals_config_loader import (  # noqa: F401, E402
    discover_skill_adjacent_eval_files,
    load_config,
    load_config_from_dir,
    load_skill_body_from_path,
    resolve_system_prompt_for_test,
)
from run_evals_evidence import raise_for_evaluation_errors  # noqa: E402
from run_evals_judge import build_llm_judge  # noqa: E402
from run_evals_judge_calibration import (  # noqa: E402
    judge_agreement,
    load_calibration_cases,
)
from run_evals_reporting import (  # noqa: F401, E402
    list_categories,
    print_ab_summary,
    print_calibration_summary,
    print_epoch_summary,
    print_results,
)
from run_evals_sampling import (  # noqa: E402
    aggregate_repeated_runs,
    build_epoch_enriched_baseline,
)
from run_evals_test_runner import (  # noqa: F401, E402
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
    args = parse_arguments()

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

    if args.calibrate_judge:
        judge_model = config.get("settings", {}).get("judge_model", "opus")
        judge = build_llm_judge(judge_model, run_claude_cli)
        agreement = judge_agreement(load_calibration_cases(), judge)
        passed = print_calibration_summary(agreement)
        sys.exit(0 if passed else 1)

    print("Running agent evaluations (Claude Max - no API cost)...")
    if args.dry_run:
        print("   (dry run - no claude calls)")

    if args.ab:
        with temporary_eval_worktree():
            comparison = run_instruction_loading_experiment(
                config,
                category=args.category,
                max_workers_override=args.workers,
                epochs=args.epochs,
                comparison_ref=args.compare_ref,
                dry_run=args.dry_run,
            )
        print_ab_summary(comparison)
        if args.save_ab_profile:
            save_ab_profile(comparison, args.category, args.compare_ref)
        sys.exit(0)

    if args.epochs > 1:
        with temporary_eval_worktree():
            results_per_epoch = []
            for epoch_index in range(args.epochs):
                print(f"\n--- epoch {epoch_index + 1}/{args.epochs} ---")
                epoch_results = run_tests(
                    config,
                    category=args.category,
                    test_name=args.test,
                    dry_run=args.dry_run,
                    smoke_only=args.smoke,
                    max_workers_override=args.workers,
                )
                raise_for_evaluation_errors(epoch_results, "repeated evaluation")
                results_per_epoch.append(epoch_results)
        per_test = aggregate_repeated_runs(results_per_epoch)
        no_hard_failures = print_epoch_summary(per_test, args.epochs)
        if args.save_baseline:
            baseline = build_epoch_enriched_baseline(
                per_test,
                args.epochs,
                get_current_git_commit(),
                datetime.now(timezone.utc).isoformat(),
            )
            write_baseline(
                merge_baseline_snapshot(baseline) if args.category else baseline
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
        save_baseline(results, merge=args.category is not None)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
