from math import comb
from random import Random


def mcnemar_exact_p_value(discordant_a_only: int, discordant_b_only: int) -> float:
    total_discordant = discordant_a_only + discordant_b_only
    if total_discordant == 0:
        return 1.0
    smaller_tail = min(discordant_a_only, discordant_b_only)
    one_sided = sum(comb(total_discordant, i) for i in range(smaller_tail + 1)) * (
        0.5**total_discordant
    )
    return min(1.0, 2.0 * one_sided)


def paired_comparison(
    variant_a: dict[str, bool],
    variant_b: dict[str, bool],
    alpha: float = 0.05,
) -> dict:
    shared_names = sorted(set(variant_a) & set(variant_b))
    both_pass = 0
    a_only_wins = 0
    b_only_wins = 0
    both_fail = 0
    for name in shared_names:
        passed_under_a = variant_a[name]
        passed_under_b = variant_b[name]
        if passed_under_a and passed_under_b:
            both_pass += 1
        elif passed_under_a and not passed_under_b:
            a_only_wins += 1
        elif not passed_under_a and passed_under_b:
            b_only_wins += 1
        else:
            both_fail += 1

    n_paired = len(shared_names)
    variant_a_pass_rate = (both_pass + a_only_wins) / n_paired if n_paired else 0.0
    variant_b_pass_rate = (both_pass + b_only_wins) / n_paired if n_paired else 0.0
    p_value = mcnemar_exact_p_value(a_only_wins, b_only_wins)

    return {
        "method": "mcnemar_exact",
        "n_paired": n_paired,
        "variant_a_pass_rate": variant_a_pass_rate,
        "variant_b_pass_rate": variant_b_pass_rate,
        "delta": variant_a_pass_rate - variant_b_pass_rate,
        "a_only_wins": a_only_wins,
        "b_only_wins": b_only_wins,
        "both_pass": both_pass,
        "both_fail": both_fail,
        "p_value": p_value,
        "significant": p_value < alpha,
    }


def percentile(sorted_values: list[float], quantile: float) -> float:
    if not sorted_values:
        return 0.0
    index = round((len(sorted_values) - 1) * quantile)
    return sorted_values[index]


def paired_hierarchical_bootstrap(
    variant_a: dict[str, list[bool]],
    variant_b: dict[str, list[bool]],
    iterations: int = 10_000,
    seed: int = 0,
    alpha: float = 0.05,
) -> dict:
    shared_names = sorted(set(variant_a) & set(variant_b))
    for name in shared_names:
        if len(variant_a[name]) != len(variant_b[name]):
            raise ValueError("paired variants need the same number of generations")
        if not variant_a[name]:
            raise ValueError("paired variants need at least one generation per case")

    if not shared_names:
        return {
            "method": "paired_hierarchical_bootstrap",
            "n_paired": 0,
            "epochs": 0,
            "sample_pairs": 0,
            "variant_a_pass_rate": 0.0,
            "variant_b_pass_rate": 0.0,
            "delta": 0.0,
            "lower_bound": 0.0,
            "upper_bound": 0.0,
            "significant": False,
            "candidate_hard_failures": [],
            "control_hard_failures": [],
            "candidate_case_outcomes": {},
            "control_case_outcomes": {},
        }

    def macro_pass_rate(samples: dict[str, list[bool]]) -> float:
        return sum(
            sum(samples[name]) / len(samples[name]) for name in shared_names
        ) / len(shared_names)

    variant_a_pass_rate = macro_pass_rate(variant_a)
    variant_b_pass_rate = macro_pass_rate(variant_b)
    random = Random(seed)
    bootstrap_deltas = []
    for _ in range(iterations):
        sampled_cases = [random.choice(shared_names) for _ in shared_names]
        case_deltas = []
        for name in sampled_cases:
            generation_count = len(variant_a[name])
            sampled_generations = [
                random.randrange(generation_count) for _ in range(generation_count)
            ]
            a_rate = sum(variant_a[name][index] for index in sampled_generations) / len(
                sampled_generations
            )
            b_rate = sum(variant_b[name][index] for index in sampled_generations) / len(
                sampled_generations
            )
            case_deltas.append(a_rate - b_rate)
        bootstrap_deltas.append(sum(case_deltas) / len(case_deltas))

    bootstrap_deltas.sort()
    lower_bound = percentile(bootstrap_deltas, alpha / 2)
    upper_bound = percentile(bootstrap_deltas, 1 - alpha / 2)
    return {
        "method": "paired_hierarchical_bootstrap",
        "n_paired": len(shared_names),
        "epochs": len(variant_a[shared_names[0]]),
        "sample_pairs": sum(len(variant_a[name]) for name in shared_names),
        "variant_a_pass_rate": variant_a_pass_rate,
        "variant_b_pass_rate": variant_b_pass_rate,
        "delta": variant_a_pass_rate - variant_b_pass_rate,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "significant": lower_bound > 0 or upper_bound < 0,
        "candidate_hard_failures": [
            name for name in shared_names if not any(variant_a[name])
        ],
        "control_hard_failures": [
            name for name in shared_names if not any(variant_b[name])
        ],
        "candidate_case_outcomes": {name: variant_a[name] for name in shared_names},
        "control_case_outcomes": {name: variant_b[name] for name in shared_names},
    }
