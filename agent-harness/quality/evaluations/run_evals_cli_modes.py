from datetime import datetime, timezone

from run_evals_ab import run_instruction_loading_experiment
from run_evals_ab_record import save_ab_profile
from run_evals_baseline_record import (
    get_current_git_commit,
    merge_baseline_snapshot,
    save_baseline,
    write_baseline,
)
from run_evals_evidence import raise_for_evaluation_errors
from run_evals_judge import build_llm_judge
from run_evals_judge_calibration import judge_agreement, load_calibration_cases
from run_evals_provider_usage import provider_usage_summary
from run_evals_reporting import (
    print_ab_summary,
    print_calibration_summary,
    print_epoch_summary,
    print_provider_usage,
    print_results,
)
from run_evals_sampling import aggregate_repeated_runs, build_epoch_enriched_baseline
from run_evals_subject_port import build_provider_invoker
from run_evals_suite_runner import run_tests
from run_evals_worktree_and_environment import temporary_eval_worktree


def collect_and_print_provider_usage() -> dict:
    token_usage = provider_usage_summary()
    print_provider_usage(token_usage)
    return token_usage


def run_judge_calibration(config: dict, args) -> int:
    settings = config.get("settings", {})
    judge = build_llm_judge(
        settings["judge_models"][args.judge_harness],
        build_provider_invoker(
            args.judge_harness,
            settings.get("timeout_seconds", 120),
            settings.get("judge_reasoning_efforts", {}).get(args.judge_harness),
        ),
    )
    agreement = judge_agreement(
        load_calibration_cases(),
        judge,
        max_workers=args.workers or settings.get("parallel_workers", 4),
    )
    passed = print_calibration_summary(agreement)
    collect_and_print_provider_usage()
    return 0 if passed else 1


def run_ab_evaluation(config: dict, args, execution_profile: dict) -> int:
    with temporary_eval_worktree():
        comparison = run_instruction_loading_experiment(
            config,
            category=args.category,
            max_workers_override=args.workers,
            epochs=args.epochs,
            comparison_ref=args.compare_ref,
            dry_run=args.dry_run,
            harness=args.harness,
            judge_harness=args.judge_harness,
        )
    print_ab_summary(comparison)
    token_usage = collect_and_print_provider_usage()
    if args.save_ab_profile:
        save_ab_profile(
            comparison,
            args.category,
            args.compare_ref,
            execution_profile,
            token_usage,
        )
    return 0


def run_repeated_evaluation(config: dict, args, execution_profile: dict) -> int:
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
                harness=args.harness,
                judge_harness=args.judge_harness,
            )
            raise_for_evaluation_errors(epoch_results, "repeated evaluation")
            results_per_epoch.append(epoch_results)
    per_test = aggregate_repeated_runs(results_per_epoch)
    no_hard_failures = print_epoch_summary(per_test, args.epochs)
    token_usage = collect_and_print_provider_usage()
    if args.save_baseline:
        baseline = build_epoch_enriched_baseline(
            per_test,
            args.epochs,
            get_current_git_commit(),
            datetime.now(timezone.utc).isoformat(),
            execution_profile,
            token_usage,
        )
        write_baseline(
            merge_baseline_snapshot(baseline, execution_profile, token_usage)
            if args.category
            else baseline
        )
    return 0 if no_hard_failures else 1


def run_single_evaluation(config: dict, args, execution_profile: dict) -> int:
    with temporary_eval_worktree():
        results = run_tests(
            config,
            category=args.category,
            test_name=args.test,
            dry_run=args.dry_run,
            smoke_only=args.smoke,
            max_workers_override=args.workers,
            harness=args.harness,
            judge_harness=args.judge_harness,
        )
    all_passed = print_results(results, harness=args.harness)
    token_usage = collect_and_print_provider_usage()
    if args.save_baseline:
        save_baseline(
            results,
            execution_profile,
            token_usage,
            merge=args.category is not None,
        )
    return 0 if all_passed else 1
