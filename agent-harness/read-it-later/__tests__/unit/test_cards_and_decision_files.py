import copy

import pytest
from hypothesis import given
from hypothesis import strategies as st

from proposals.cards import (
    CARD_FIELDS,
    CardsInvalid,
    example_cards_document,
    validated_cards_document,
)
from proposals.decision_files import parse_decision_file, render_decision_file

free_text = st.text(max_size=80)


def example() -> dict:
    return copy.deepcopy(example_cards_document())


def test_the_published_example_is_a_valid_cards_document():
    assert len(validated_cards_document(example())) == 1


@given(st.sampled_from(sorted(CARD_FIELDS)))
def test_every_missing_card_field_is_named(field_name):
    document = example()
    del document["groups"][0]["cards"][0][field_name]

    with pytest.raises(CardsInvalid) as invalid:
        validated_cards_document(document)
    assert any(field_name in problem for problem in invalid.value.problems)


def test_a_file_card_needs_its_entry_draft_and_a_session_card_needs_a_session():
    document = example()
    del document["groups"][0]["cards"][1]["entry"]
    del document["groups"][0]["session"]

    with pytest.raises(CardsInvalid) as invalid:
        validated_cards_document(document)
    assert any(".entry" in problem for problem in invalid.value.problems)
    assert any(".session" in problem for problem in invalid.value.problems)


def test_a_capture_may_sit_in_only_one_card():
    document = example()
    document["groups"].append(copy.deepcopy(document["groups"][0]))
    document["groups"][1]["topic_slug"] = "another-topic"

    with pytest.raises(CardsInvalid, match="more than one card"):
        validated_cards_document(document)


@given(st.sampled_from(["Has Caps", "trailing-", "", "under_score", "a--b"]))
def test_topic_slugs_are_lowercase_hyphenated_words(topic_slug):
    document = example()
    document["groups"][0]["topic_slug"] = topic_slug

    with pytest.raises(CardsInvalid, match="topic_slug"):
        validated_cards_document(document)


@given(free_text, free_text, free_text, st.lists(free_text, max_size=3))
def test_any_card_text_survives_a_round_trip_through_the_decision_file(
    tldr, note, reason, evidence
):
    group = example()["groups"][0]
    card = group["cards"][0]
    card.update(
        tldr=tldr,
        lucas_note=note,
        reason=reason,
        covered_evidence=evidence,
        added_at="2026-11-08T21:00:00+00:00",
    )

    assert parse_decision_file(render_decision_file(group)) == group


@given(st.text(alphabet="|\n`*", min_size=1, max_size=20))
def test_table_breaking_characters_never_add_or_split_a_row(hostile_text):
    group = example()["groups"][0]
    group["cards"][0]["tldr"] = hostile_text
    table_rows = [
        line
        for line in render_decision_file(group).splitlines()
        if line.startswith("| ")
    ]

    assert len(table_rows) == 1 + len(group["cards"])
