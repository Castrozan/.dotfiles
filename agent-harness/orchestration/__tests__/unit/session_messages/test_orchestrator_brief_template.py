import pytest
from orchestrator_cli.session_messages.brief_template import brief_problems
from session_message_test_support import brief


def test_a_brief_stating_outcomes_passes_and_one_dictating_steps_is_refused():
    assert brief_problems(brief(), "kira") == []
    numbered = "1. Build the gate script\n2. Deny glab\n3. Rehearse, then disconnect"
    problems = brief_problems(brief(done_when=numbered), "kira")
    assert len(problems) == 3
    assert all("orders steps" in problem for problem in problems)
    inline = "- Build it: 1) the gate script; 2) deny glab"
    assert len(brief_problems(brief(done_when=inline), "kira")) == 1


@pytest.mark.parametrize(
    "step", ["- 1. Build the gate", "(1) build the gate", "Step 1: build the gate"]
)
def test_every_common_way_of_numbering_a_step_is_refused(step):
    assert len(brief_problems(brief(done_when=step), "kira")) == 1


@pytest.mark.parametrize(
    "outcome",
    ["- 1.2 GiB freed on chise", "- Version 2.1 lands", "10:30 is the cutoff"],
)
def test_numbers_that_are_not_steps_pass(outcome):
    assert brief_problems(brief(done_when=outcome), "kira") == []


def test_lucas_numbered_words_and_fenced_lines_are_not_dictated_steps():
    words = "> 1. No need to clone, it's on the disk already.\n> 2. I need info."
    assert brief_problems(brief(words=words), "kira") == []
    nested = "````\n```\n1. sample output\n```\n````\n- Rehearsal evidence exists"
    assert brief_problems(brief(done_when=nested), "kira") == []


def test_a_brief_missing_a_template_heading_or_the_remote_contract_is_refused():
    without_goal = brief().replace("## Goal", "## Background")
    problems = brief_problems(without_goal, None)
    assert any("missing or out of order: Goal" in problem for problem in problems)
    for host in ("fuji", "kir"):
        assert brief_problems(brief(), host) == [
            f"the Contract section must show the session `--reply-host {host}`"
        ]


@pytest.mark.parametrize("context", ["", "```\nprivate\n```"])
def test_a_brief_without_context_for_the_session_is_refused(context):
    assert brief_problems(brief(context=context), "kira") == [
        "the Context section must say whose work this is, where its results may be "
        "published, and which requirements are hard and which are open"
    ]
    no_heading = brief().replace("## Context", "## Background")
    assert any("Context" in problem for problem in brief_problems(no_heading, "kira"))
