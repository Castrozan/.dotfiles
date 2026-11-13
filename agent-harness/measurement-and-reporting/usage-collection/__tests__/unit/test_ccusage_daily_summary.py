import math
from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ccusage_daily_summary import CcusageDocumentError, summarize_ccusage_daily

MODELS = ["claude-haiku-4-5", "claude-opus-4-8", "claude-sonnet-4-6"]
FIELDS = [
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
]
COUNTER_NAMES = [
    "inputTokens",
    "outputTokens",
    "cacheReadTokens",
    "cacheCreationTokens",
]


def breakdown(model="claude-opus-4-8", cost=0.5, counts=(1, 2, 3, 4)):
    return {
        "modelName": model,
        "cost": cost,
        **dict(zip(COUNTER_NAMES, counts, strict=True)),
    }


def document(*days):
    return {"daily": [{"date": d, "modelBreakdowns": list(parts)} for d, parts in days]}


CANONICAL = document(
    ("2026-06-16", [breakdown("claude-opus-4-8", 1.25, (10, 20, 30, 40))]),
    (
        "2026-06-17",
        [
            breakdown("claude-opus-4-8", 0.5, (1, 2, 3, 4)),
            breakdown("claude-haiku-4-5", 0.25, (5, 6, 7, 8)),
        ],
    ),
)


def with_field(**changes):
    return document(("2026-06-17", [{**breakdown(), **changes}]))


DUPLICATE_DATE = document(("2026-06-17", [breakdown()]), ("2026-06-17", [breakdown()]))
DUPLICATE_MODEL = document(("2026-06-17", [breakdown(), breakdown()]))
MALFORMED = [
    pytest.param(["not", "an", "object"], id="non-object"),
    pytest.param({"other": []}, id="missing-daily"),
    pytest.param({"daily": [{"date": "2026-06-17"}]}, id="no-breakdowns"),
    pytest.param(document(("2026-6-1", [breakdown()])), id="non-canonical-date"),
    pytest.param(document(("2026-02-30", [breakdown()])), id="impossible-date"),
    pytest.param(DUPLICATE_DATE, id="duplicate-date"),
    pytest.param(DUPLICATE_MODEL, id="duplicate-model"),
    pytest.param(with_field(modelName=""), id="empty-model-name"),
    pytest.param(with_field(inputTokens=True), id="boolean-token"),
    pytest.param(with_field(outputTokens=1.5), id="fractional-token"),
    pytest.param(with_field(cacheReadTokens=-1), id="negative-token"),
    pytest.param(with_field(cacheCreationTokens=None), id="missing-token"),
    pytest.param(with_field(cost=math.nan), id="nan-cost"),
    pytest.param(with_field(cost=-0.5), id="negative-cost"),
]


class TestSummarizeCcusageDaily:
    def test_empty_daily_input_summarizes_to_none(self):
        assert summarize_ccusage_daily(document()) is None

    def test_model_totals_sum_all_four_token_categories_and_cost(self):
        totals = summarize_ccusage_daily(CANONICAL)["model_usage_totals"]
        assert totals == {
            "claude-haiku-4-5": {
                "input_tokens": 5,
                "output_tokens": 6,
                "cache_read_input_tokens": 7,
                "cache_creation_input_tokens": 8,
                "cost_usd": 0.25,
            },
            "claude-opus-4-8": {
                "input_tokens": 11,
                "output_tokens": 22,
                "cache_read_input_tokens": 33,
                "cache_creation_input_tokens": 44,
                "cost_usd": 1.75,
            },
        }

    def test_daily_tokens_and_dates_come_from_the_daily_entries(self):
        summary = summarize_ccusage_daily(CANONICAL)
        assert summary["daily_model_tokens"] == [
            {"date": "2026-06-16", "tokens_by_model": {"claude-opus-4-8": 100}},
            {
                "date": "2026-06-17",
                "tokens_by_model": {"claude-haiku-4-5": 26, "claude-opus-4-8": 10},
            },
        ]
        assert summary["stats_last_computed_date"] == "2026-06-17"
        assert summary["model_usage_first_date"] == "2026-06-16"
        assert summary["model_usage_source"] == "ccusage-offline"

    @pytest.mark.parametrize("malformed", MALFORMED)
    def test_malformed_document_is_rejected_not_defaulted(self, malformed):
        with pytest.raises(CcusageDocumentError):
            summarize_ccusage_daily(malformed)


DATE_TEXT = st.dates(min_value=date(2026, 1, 1), max_value=date(2026, 12, 31))
COUNT = st.integers(min_value=0, max_value=10**12)
BREAKDOWN = st.fixed_dictionaries(
    {
        "modelName": st.sampled_from(MODELS),
        "inputTokens": COUNT,
        "outputTokens": COUNT,
        "cacheReadTokens": COUNT,
        "cacheCreationTokens": COUNT,
        "cost": st.floats(min_value=0, max_value=10**6, allow_nan=False),
    }
)
DAY = st.tuples(
    DATE_TEXT.map(date.isoformat),
    st.lists(BREAKDOWN, unique_by=lambda item: item["modelName"], max_size=3),
)
DOCUMENT = st.lists(DAY, unique_by=lambda day: day[0], min_size=1, max_size=6).map(
    lambda days: document(*days)
)


def model_token_totals(summary):
    if summary is None:
        return {}
    return {
        name: {field: totals[field] for field in FIELDS}
        for name, totals in summary["model_usage_totals"].items()
    }


@given(DOCUMENT)
def test_every_reported_counter_is_nonnegative(source):
    summary = summarize_ccusage_daily(source)
    values = [v for t in summary["model_usage_totals"].values() for v in t.values()]
    values += [
        v for d in summary["daily_model_tokens"] for v in d["tokens_by_model"].values()
    ]
    assert all(value >= 0 for value in values)


@given(DOCUMENT)
def test_token_categories_are_conserved_and_dates_are_extremes(source):
    summary = summarize_ccusage_daily(source)
    items = [item for day in source["daily"] for item in day["modelBreakdowns"]]
    expected = sum(sum(item[name] for name in COUNTER_NAMES) for item in items)
    by_model = sum(
        sum(t[field] for field in FIELDS)
        for t in summary["model_usage_totals"].values()
    )
    by_day = sum(
        sum(d["tokens_by_model"].values()) for d in summary["daily_model_tokens"]
    )
    dates = [day["date"] for day in source["daily"]]
    assert by_model == by_day == expected
    assert summary["stats_last_computed_date"] == max(dates)
    assert summary["model_usage_first_date"] == min(dates)


@given(DOCUMENT, st.data())
def test_summary_is_invariant_under_day_and_model_reordering(source, data):
    shuffled = [
        {
            "date": day["date"],
            "modelBreakdowns": data.draw(st.permutations(day["modelBreakdowns"])),
        }
        for day in data.draw(st.permutations(source["daily"]))
    ]
    assert summarize_ccusage_daily({"daily": shuffled}) == summarize_ccusage_daily(
        source
    )


@given(DOCUMENT, st.integers(min_value=0, max_value=6))
def test_splitting_days_into_two_documents_preserves_token_totals(source, cut):
    combined = {}
    for part in (source["daily"][:cut], source["daily"][cut:]):
        for name, totals in model_token_totals(
            summarize_ccusage_daily({"daily": part})
        ).items():
            accumulated = combined.setdefault(name, dict.fromkeys(FIELDS, 0))
            for field in FIELDS:
                accumulated[field] += totals[field]
    assert combined == model_token_totals(summarize_ccusage_daily(source))
