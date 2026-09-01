#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_evals_arguments import parse_arguments  # noqa: E402
from run_evals_baseline import check_baseline_for_regression  # noqa: E402
from run_evals_cli_modes import (  # noqa: E402
    run_ab_evaluation,
    run_judge_calibration,
    run_repeated_evaluation,
    run_single_evaluation,
)
from run_evals_config_loader import load_config  # noqa: E402
from run_evals_execution_profile import build_execution_profile  # noqa: E402
from run_evals_provider_usage import reset_provider_usage  # noqa: E402
from run_evals_reporting import list_categories  # noqa: E402
from run_evals_subject_port import resolve_node_runtime  # noqa: E402


def main():
    args = parse_arguments()
    config = load_config(Path(args.config))
    settings = config.get("settings", {})
    canonical_execution_profile = build_execution_profile(
        settings,
        settings["canonical_subject_harness"],
        settings["canonical_judge_harness"],
    )
    execution_profile = build_execution_profile(
        settings, args.harness, args.judge_harness
    )

    if args.check_baseline:
        passed = check_baseline_for_regression(canonical_execution_profile)
        sys.exit(0 if passed else 1)
    if args.list:
        list_categories(config)
        sys.exit(0)

    reset_provider_usage()
    if not args.dry_run:
        try:
            resolve_node_runtime()
        except RuntimeError as error:
            print(f"Error: {error}")
            print("Run 'rebuild' to install the agent evaluation provider runtime")
            sys.exit(1)

    if args.calibrate_judge:
        sys.exit(run_judge_calibration(config, args))

    print(
        f"Running agent evaluations with {args.harness} subject "
        f"and {args.judge_harness} judge..."
    )
    if args.dry_run:
        print("   (dry run - no model calls)")

    if args.ab:
        exit_code = run_ab_evaluation(config, args, execution_profile)
    elif args.epochs > 1:
        exit_code = run_repeated_evaluation(config, args, execution_profile)
    else:
        exit_code = run_single_evaluation(config, args, execution_profile)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
