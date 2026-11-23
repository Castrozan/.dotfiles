import pytest
from hypothesis import given
from hypothesis import strategies as st
from orchestration_test_support import heartbeat_text
from orchestrator_cli.document_fields import InvalidPeerDocument
from orchestrator_cli.heartbeats.template import (
    HEARTBEAT_LINE_LIMITS,
    HEARTBEAT_STATES,
    HEARTBEAT_TEMPLATE,
    parsed_heartbeat,
    rendered_heartbeat,
)

ONE_LINE_CHARACTERS = st.characters(blacklist_categories=("Cc", "Cs", "Zl", "Zp"))


def one_line(max_size=60, extra_forbidden=""):
    return (
        st.text(ONE_LINE_CHARACTERS, min_size=1, max_size=max_size)
        .map(str.strip)
        .filter(lambda text: bool(text) and not set(text) & set(extra_forbidden))
    )


@st.composite
def heartbeats(draw):
    lines = {
        field: draw(one_line(limit)) for field, limit in HEARTBEAT_LINE_LIMITS.items()
    }
    decisions = draw(st.lists(one_line(), max_size=3))
    states = [state for state in HEARTBEAT_STATES if decisions or state != "blocked"]
    done = st.fixed_dictionaries(
        {"claim": one_line(), "evidence": one_line(extra_forbidden="()")}
    )
    return {
        **lines,
        "state": draw(st.sampled_from(states)),
        "done": draw(st.lists(done, max_size=3)),
        "unverified": draw(st.lists(one_line(), max_size=3)),
        "open_decisions": decisions,
    }


@given(heartbeats())
def test_every_valid_heartbeat_survives_rendering_and_parsing_unchanged(heartbeat):
    assert parsed_heartbeat(rendered_heartbeat(heartbeat)) == heartbeat


@given(st.text(max_size=400))
def test_any_text_either_parses_or_is_refused_with_a_reason(text):
    try:
        parsed = parsed_heartbeat(text)
    except InvalidPeerDocument as refusal:
        assert str(refusal)
    else:
        assert parsed_heartbeat(rendered_heartbeat(parsed)) == parsed


@given(heartbeats(), st.data())
def test_dropping_any_template_line_is_refused(heartbeat, data):
    lines = [line for line in rendered_heartbeat(heartbeat).splitlines() if line]
    structural = [
        index for index, line in enumerate(lines) if not line.startswith("- ")
    ]
    dropped = data.draw(st.sampled_from(structural))
    with pytest.raises(InvalidPeerDocument):
        parsed_heartbeat("\n".join(lines[:dropped] + lines[dropped + 1 :]))


def test_the_printed_template_is_the_shape_the_parser_reads():
    filled = HEARTBEAT_TEMPLATE.replace(
        "<working | waiting | blocked | done>", "working"
    )
    parsed = parsed_heartbeat(
        filled.replace(
            "(evidence: <commit, path, command or link>)", "(evidence: a1b2c3d)"
        )
    )
    assert parsed["state"] == "working" and parsed["done"][0]["evidence"] == "a1b2c3d"


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("", "starts with the line # Heartbeat"),
        (heartbeat_text().replace("## Not verified", "## Risks"), "in that order"),
        (
            heartbeat_text().replace("- the binary", "the binary"),
            "neither a `## ` heading",
        ),
        (heartbeat_text(state="blocked"), "lists the decisions it waits on"),
        (heartbeat_text(doing="x" * 121), "over its limit of 120"),
        (
            heartbeat_text().replace("evidence: a1b2c3d", "evidence: (a1)"),
            "no parentheses",
        ),
    ],
)
def test_each_refusal_names_what_to_fix(text, reason):
    with pytest.raises(InvalidPeerDocument, match=reason.replace("(", r"\(")):
        parsed_heartbeat(text)
