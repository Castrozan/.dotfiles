from turn_cost import CACHE_READ_WEIGHT, CACHE_WRITE_ONE_HOUR_WEIGHT, OUTPUT_WEIGHT

COMPACTION_SUMMARY_TOKENS = 8000
REPLAY_THRESHOLDS = (400_000, 300_000, 200_000, 150_000, 100_000, 75_000, 50_000)


def replay_session(turns, threshold):
    baseline_context = turns[0].context
    context = previous_context = baseline_context
    cost = 0.0
    compactions = 0
    for turn in turns:
        growth = max(turn.context - previous_context, 0)
        previous_context = turn.context
        context += growth
        cost += (
            CACHE_READ_WEIGHT * context
            + CACHE_WRITE_ONE_HOUR_WEIGHT * growth
            + OUTPUT_WEIGHT * turn.output
        )
        if context >= threshold:
            rebuilt_context = baseline_context + COMPACTION_SUMMARY_TOKENS
            cost += (
                CACHE_READ_WEIGHT * context
                + OUTPUT_WEIGHT * COMPACTION_SUMMARY_TOKENS
                + CACHE_WRITE_ONE_HOUR_WEIGHT * rebuilt_context
            )
            context = rebuilt_context
            compactions += 1
    return cost, compactions


def replay_totals(sessions, threshold):
    replayed = [replay_session(session.turns, threshold) for session in sessions]
    return sum(cost for cost, _ in replayed), sum(count for _, count in replayed)
