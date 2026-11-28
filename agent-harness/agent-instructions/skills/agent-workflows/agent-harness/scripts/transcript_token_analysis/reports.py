import collections
import statistics

from compaction_replay import REPLAY_THRESHOLDS, replay_totals
from turn_cost import (
    CACHE_READ_WEIGHT,
    CACHE_WRITE_FIVE_MINUTE_WEIGHT,
    CACHE_WRITE_ONE_HOUR_WEIGHT,
    OUTPUT_WEIGHT,
)

TURN_BUCKETS = ((0, 50), (50, 200), (200, 500), (500, 10**9))


def share(part, whole):
    return f"{part / whole * 100:.0f}%" if whole else "n/a"


def cost_mix(turns):
    return {
        "fresh_input": sum(turn.fresh_input for turn in turns),
        "cache_read": CACHE_READ_WEIGHT * sum(turn.cache_read for turn in turns),
        "cache_write": sum(
            CACHE_WRITE_ONE_HOUR_WEIGHT * turn.cache_write_one_hour
            + CACHE_WRITE_FIVE_MINUTE_WEIGHT * turn.cache_write_five_minute
            for turn in turns
        ),
        "output": OUTPUT_WEIGHT * sum(turn.output for turn in turns),
    }


def report_session_length_buckets(sessions, total_cost):
    for low, high in TURN_BUCKETS:
        bucket = [session for session in sessions if low <= len(session.turns) < high]
        bucket_cost = sum(session.weighted_cost for session in bucket)
        print(
            f"sessions with {low}-{high} turns: n={len(bucket)} cost={share(bucket_cost, total_cost)}"
        )


def report_preamble(sessions, turns):
    first_contexts = sorted(session.turns[0].context for session in sessions)
    print(
        "first-turn context median/p10/p90:",
        int(statistics.median(first_contexts)),
        first_contexts[len(first_contexts) // 10],
        first_contexts[9 * len(first_contexts) // 10],
    )
    preamble_tokens = sum(
        session.turns[0].context * len(session.turns) for session in sessions
    )
    all_tokens = sum(turn.context for turn in turns)
    print("preamble share of context tokens:", share(preamble_tokens, all_tokens))
    print("average context per turn:", all_tokens // len(turns))


def report_summary(sessions):
    total_cost = sum(session.weighted_cost for session in sessions)
    turns = [turn for session in sessions for turn in session.turns]
    print(f"sessions={len(sessions)} turns={len(turns)}")
    for name, value in cost_mix(turns).items():
        print(f"cost mix {name}: {share(value, total_cost)}")
    report_session_length_buckets(sessions, total_cost)
    report_preamble(sessions, turns)
    cache_read_by_model = collections.Counter()
    cost_by_project = collections.Counter()
    for session in sessions:
        cache_read_by_model[session.model] += sum(
            turn.cache_read for turn in session.turns
        )
        cost_by_project[session.project] += session.weighted_cost
    for model, tokens in cache_read_by_model.most_common():
        print(f"cache read {model}: {tokens / 1e6:.0f}M")
    for project, cost in cost_by_project.most_common(5):
        print(f"project {share(cost, total_cost)} {project}")


def report_tools(sessions):
    text_bytes = sum(
        (session.tool_text_bytes for session in sessions), collections.Counter()
    )
    image_bytes = sum(
        (session.tool_image_bytes for session in sessions), collections.Counter()
    )
    calls = sum((session.tool_calls for session in sessions), collections.Counter())
    ranked = sorted(calls, key=lambda tool: -(text_bytes[tool] + image_bytes[tool]))
    for tool in ranked[:10]:
        print(
            f"{tool}: calls={calls[tool]} text={text_bytes[tool] / 1e6:.1f}MB "
            f"image={image_bytes[tool] / 1e6:.1f}MB"
        )
    reads_total = sum(session.reads_total for session in sessions)
    reads_repeated = sum(session.reads_repeated for session in sessions)
    print(
        f"Read repeats of a file already read in the same session: {reads_repeated} of {reads_total}"
    )


def report_replay(sessions, current_threshold):
    observed = sum(session.compactions for session in sessions)
    turn_count = sum(len(session.turns) for session in sessions)
    baseline_cost, baseline_compactions = replay_totals(sessions, current_threshold)
    print(
        f"validation: observed compactions={observed} replayed at {current_threshold}={baseline_compactions}"
    )
    for threshold in REPLAY_THRESHOLDS:
        cost, compactions = replay_totals(sessions, threshold)
        print(
            f"threshold={threshold // 1000}k compactions={compactions} "
            f"per_1000_turns={compactions / turn_count * 1000:.1f} "
            f"relative_cost={share(cost, baseline_cost)}"
        )
