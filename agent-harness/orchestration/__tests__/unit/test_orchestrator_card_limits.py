import pytest
from hypothesis import given
from hypothesis import strategies as st
from orchestration_test_support import valid_card_document
from orchestrator_cli.decisions import card_limits
from orchestrator_cli.decisions.cards import escalated_card, new_decision_card
from orchestrator_cli.decisions.rendering import CARD_WIDTH, rendered_card
from orchestrator_cli.document_fields import InvalidPeerDocument

MAXIMUM_RENDERED_LINES = 90

line_text = st.text(
    alphabet=st.characters(categories=("L", "N", "Zs")), min_size=1
).filter(str.strip)


def bounded(limit):
    return line_text.map(lambda text: text[:limit]).filter(str.strip)


def text_fields(limits):
    return st.fixed_dictionaries({f: bounded(n) for f, n in limits.items()})


def filed(document):
    return new_decision_card(document, "Voyager", "wW:p1", "Medea")


def card_documents():
    text_limits = dict(card_limits.CARD_TEXT_LIMITS)
    del text_limits["recommendation"]
    items = bounded(card_limits.LIST_ITEM_LIMIT)
    return st.builds(
        lambda fields, first, second, evidence, assumptions: {
            **fields,
            "options": [
                {**first, "label": "first"},
                {**second, "label": "second"},
            ],
            "recommendation": "first",
            "evidence": evidence,
            "unverified_assumptions": assumptions,
            "reversible": True,
        },
        text_fields(text_limits),
        text_fields(card_limits.OPTION_TEXT_LIMITS),
        text_fields(card_limits.OPTION_TEXT_LIMITS),
        st.lists(items, min_size=1, max_size=card_limits.CARD_LIST_LIMITS["evidence"]),
        st.lists(
            items, max_size=card_limits.CARD_LIST_LIMITS["unverified_assumptions"]
        ),
    )


@given(card_documents())
def test_every_fileable_card_fits_one_reply_at_the_terminal_width(document):
    lines = rendered_card(filed(document)).splitlines()
    assert max(map(len, lines)) <= CARD_WIDTH
    assert len(lines) <= MAXIMUM_RENDERED_LINES


@pytest.mark.parametrize(
    "field", [f for f in card_limits.CARD_TEXT_LIMITS if f != "recommendation"]
)
def test_an_oversized_or_multiline_field_is_refused_by_name(field):
    limit = card_limits.CARD_TEXT_LIMITS[field]
    with pytest.raises(InvalidPeerDocument, match=field):
        filed(valid_card_document(**{field: "x" * (limit + 1)}))
    with pytest.raises(InvalidPeerDocument, match="one line"):
        filed(valid_card_document(**{field: "| a |\n| b |"}))


def test_long_lists_and_consequences_are_refused():
    too_many = ["item"] * (card_limits.CARD_LIST_LIMITS["evidence"] + 1)
    with pytest.raises(InvalidPeerDocument, match="evidence lists 9"):
        filed(valid_card_document(evidence=too_many))
    long_option = {"label": "a", "consequence": "x" * 201}
    other_option = {"label": "b", "consequence": "fine"}
    with pytest.raises(InvalidPeerDocument, match="option consequence"):
        filed(
            valid_card_document(options=[long_option, other_option], recommendation="a")
        )


def test_the_details_file_is_named_in_the_card_lucas_reads():
    card = filed(valid_card_document(details="/home/example/hey-bot-inventory.md"))
    assert "Full detail: /home/example/hey-bot-inventory.md." in rendered_card(card)


def test_an_escalation_note_is_bounded_like_the_card_it_joins():
    card = filed(valid_card_document())
    with pytest.raises(InvalidPeerDocument, match="missing is 301"):
        escalated_card(card, "no-directive", "x" * 301)
