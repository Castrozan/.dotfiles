import argparse
from pathlib import Path

from run_evals_subject_port import ALLOWED_HARNESSES
from run_evals_suite_runner import DEFAULT_PARALLEL_WORKERS


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run agent harness evaluations")
    parser.add_argument("--smoke", action="store_true", help="Run smoke test only")
    parser.add_argument("--category", help="Run tests in specific category")
    parser.add_argument("--test", help="Run specific test by name")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    parser.add_argument("--list", action="store_true", help="List categories and tests")
    parser.add_argument(
        "--list-affected",
        action="store_true",
        help="List stale or missing baseline tests without model calls",
    )
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Checkpoint stale or missing results into the baseline",
    )
    parser.add_argument(
        "--all-tests",
        action="store_true",
        help="With --save-baseline, refresh every selected test",
    )
    parser.add_argument(
        "--check-baseline",
        action="store_true",
        help="Check committed baseline for regression without model calls",
    )
    parser.add_argument("--config", default=Path(__file__).parent / "evals")
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
        help="Repeat the suite N times to expose inconsistent behavior",
    )
    parser.add_argument(
        "--ab",
        action="store_true",
        help="Compare the instruction surface with a control",
    )
    parser.add_argument(
        "--compare-ref",
        help="With --ab, load the control instruction paths from this Git ref",
    )
    parser.add_argument(
        "--save-ab-profile",
        action="store_true",
        help="Save a repeated A/B result that passes the evidence gates",
    )
    parser.add_argument(
        "--calibrate-judge",
        action="store_true",
        help="Measure the rubric judge against labeled calibration cases",
    )
    parser.add_argument(
        "--harness",
        default="codex",
        choices=ALLOWED_HARNESSES,
        help="Agent harness to invoke as the evaluation subject (default: codex)",
    )
    parser.add_argument(
        "--judge-harness",
        default="codex",
        choices=ALLOWED_HARNESSES,
        help="Agent harness to invoke as the rubric judge (default: codex)",
    )
    args = parser.parse_args()
    if args.compare_ref and not args.ab:
        parser.error("--compare-ref requires --ab")
    if args.save_ab_profile and not (
        args.ab and args.compare_ref and args.category and args.epochs > 1
    ):
        parser.error(
            "--save-ab-profile requires --ab, --compare-ref, --category, and repeated epochs"
        )
    if args.dry_run and (args.save_baseline or args.save_ab_profile):
        parser.error("dry-run results cannot be saved as evidence")
    if args.all_tests and not args.save_baseline:
        parser.error("--all-tests requires --save-baseline")
    if args.epochs > 1 and args.save_baseline and not args.all_tests:
        parser.error("repeated baseline sampling requires explicit --all-tests")
    if args.epochs > 1 and args.save_baseline and args.test:
        parser.error("a repeated baseline snapshot cannot contain only one test")
    if args.smoke and args.save_baseline:
        parser.error("smoke results cannot replace behavioral baseline evidence")
    if args.list_affected and (args.save_baseline or args.save_ab_profile):
        parser.error("--list-affected cannot save evidence")
    if (args.save_baseline or args.save_ab_profile) and (
        args.harness != "codex" or args.judge_harness != "codex"
    ):
        parser.error("committed baseline evidence requires Codex subject and judge")
    return args
