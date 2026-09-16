import math


def wilson_score_interval(successes, total, z=1.96):
    if total == 0:
        return (0.0, 1.0)
    proportion = successes / total
    denominator = 1 + z**2 / total
    center = (proportion + z**2 / (2 * total)) / denominator
    margin = (
        z * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2))
    ) / denominator
    return (max(0.0, center - margin), min(1.0, center + margin))


def pass_at_k(num_samples, num_correct, k):
    if k <= 0 or num_samples <= 0:
        return 0.0
    if num_samples - num_correct < k:
        return 1.0
    product = 1.0
    for i in range(num_samples - num_correct + 1, num_samples + 1):
        product *= 1.0 - k / i
    return 1.0 - product


def format_pass_rate_with_confidence_interval(successes, total):
    if total == 0:
        return "Pass rate: n/a (no results)"
    pass_rate = successes / total
    lower, upper = wilson_score_interval(successes, total)
    return f"Pass rate: {pass_rate:.1%} (95% Wilson CI {lower:.1%} to {upper:.1%})"
