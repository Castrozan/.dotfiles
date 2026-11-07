def print_verdict_flips(flipped_names: list[str], case_count: int, passes: int) -> None:
    named = f" ({', '.join(flipped_names)})" if flipped_names else ""
    print(
        f"Verdict flips across {passes} passes: "
        f"{len(flipped_names)}/{case_count}{named}"
    )


def print_calibration_summary(agreement: dict) -> bool:
    print("\n" + "=" * 60)
    print("JUDGE CALIBRATION")
    print("=" * 60 + "\n")

    print(f"  Cases: {agreement['n']}")
    print(
        f"  Agreement: {agreement['agreements']}/{agreement['n']} "
        f"({agreement['accuracy']:.1%})"
    )
    print(f"  Cohen's kappa: {agreement['cohens_kappa']:.3f}")
    print(f"  Balanced accuracy: {agreement['balanced_accuracy']:.1%}")
    print(f"  Failed-case recall: {agreement['failed_case_recall']:.1%}")
    matrix = agreement["confusion_matrix"]
    print(
        f"  Confusion: TP {matrix['tp']}, TN {matrix['tn']}, "
        f"FP {matrix['fp']}, FN {matrix['fn']}"
    )
    for family, metrics in agreement["by_family"].items():
        print(
            f"  {family}: balanced {metrics['balanced_accuracy']:.1%}, "
            f"failed recall {metrics['failed_case_recall']:.1%}, "
            f"kappa {metrics['cohens_kappa']:.3f}"
        )
    if agreement["disagreements"]:
        print("  Disagreements:")
        _print_disagreements(agreement["disagreements"])
    print("-" * 60 + "\n")

    return agreement["meets_gate"]


def _print_disagreements(disagreements: list[dict]) -> None:
    for disagreement in disagreements:
        human = "PASS" if disagreement["human"] else "FAIL"
        judged = "PASS" if disagreement["judge"] else "FAIL"
        print(
            f"    - {disagreement['name']}: "
            f"human={human} judge={judged} ({disagreement['reason']})"
        )
