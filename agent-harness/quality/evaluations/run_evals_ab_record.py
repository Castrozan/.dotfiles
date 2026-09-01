import json
from datetime import datetime, timezone

from run_evals_baseline_record import (
    BASELINE_PATH,
    merge_baseline_categories,
    repeated_outcomes_category_bucket,
)
from run_evals_fingerprint import humanize_recovery_fingerprints


def save_ab_profile(
    comparison: dict,
    category: str,
    comparison_ref: str,
    execution_profile: dict,
    token_usage: dict,
    test_fingerprints: dict[str, str],
) -> None:
    if comparison.get("method") != "paired_hierarchical_bootstrap":
        raise ValueError("an evidence profile requires repeated sampling")
    if comparison.get("variant_a_pass_rate", 0) < 0.9:
        raise ValueError("candidate recovery pass rate must be at least 90%")
    if comparison.get("delta", -1) < 0:
        raise ValueError("candidate recovery pass rate must not trail control")
    if comparison.get("candidate_hard_failures"):
        raise ValueError("candidate recovery profile contains a hard-failed case")
    baseline = json.loads(BASELINE_PATH.read_text())
    baseline_token_usage = baseline.get("token_usage", {})
    fingerprints = humanize_recovery_fingerprints()
    generated_at = datetime.now(timezone.utc).isoformat()
    profile = {
        "generated_at": generated_at,
        "comparison_ref": comparison_ref,
        "epochs": comparison["epochs"],
        "paired_cases": comparison["n_paired"],
        "sample_pairs": comparison["sample_pairs"],
        "candidate_pass_rate": round(comparison["variant_a_pass_rate"], 4),
        "control_pass_rate": round(comparison["variant_b_pass_rate"], 4),
        "delta": round(comparison["delta"], 4),
        "lower_bound": round(comparison["lower_bound"], 4),
        "upper_bound": round(comparison["upper_bound"], 4),
        "candidate_hard_failures": comparison["candidate_hard_failures"],
        "candidate_cases": {
            name.split("::", 1)[-1]: {
                "passes": sum(samples),
                "samples": len(samples),
            }
            for name, samples in comparison["candidate_case_outcomes"].items()
        },
        "fingerprints": fingerprints,
        "execution_profile": execution_profile,
        "token_usage": token_usage,
    }
    baseline.setdefault("evidence_profiles", {})[category] = profile
    baseline = merge_baseline_categories(
        baseline,
        {
            category: repeated_outcomes_category_bucket(
                comparison["candidate_case_outcomes"],
                test_fingerprints,
                generated_at,
            )
        },
        execution_profile,
        baseline_token_usage,
    )
    BASELINE_PATH.write_text(json.dumps(baseline, indent=2) + "\n")
