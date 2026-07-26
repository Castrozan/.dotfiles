from math import comb


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
