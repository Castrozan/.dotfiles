import pytest
from hypothesis import given
from hypothesis import strategies as st
from orchestrator_cli.session_messages.brief_template import brief_problems
from session_message_test_support import brief

WORKFLOWS = {
    "dotfiles-fix-loop": "Fix a change that a failing scoped test reproduces",
    "dotfiles-housekeeping": "Slice one dotfiles subtree and rank its rot",
}
ONE_LINE_REASONS = st.from_regex(r"[a-z][a-z ,'-]{0,60}", fullmatch=True)
COMMAND_NAMES = st.from_regex(r"[a-z][a-z-]{0,30}", fullmatch=True)


def test_a_brief_stating_outcomes_passes_and_one_dictating_steps_is_refused():
    assert brief_problems(brief(), "kira", WORKFLOWS) == []
    numbered = "1. Build the gate script\n2. Deny glab\n3. Rehearse, then disconnect"
    problems = brief_problems(brief(done_when=numbered), "kira", WORKFLOWS)
    assert len(problems) == 3
    assert all("orders steps" in problem for problem in problems)
    inline = "- Build it: 1) the gate script; 2) deny glab"
    assert len(brief_problems(brief(done_when=inline), "kira", WORKFLOWS)) == 1


@pytest.mark.parametrize(
    "step", ["- 1. Build the gate", "(1) build the gate", "Step 1: build the gate"]
)
def test_every_common_way_of_numbering_a_step_is_refused(step):
    assert len(brief_problems(brief(done_when=step), "kira", WORKFLOWS)) == 1


@pytest.mark.parametrize(
    "outcome",
    ["- 1.2 GiB freed on chise", "- Version 2.1 lands", "10:30 is the cutoff"],
)
def test_numbers_that_are_not_steps_pass(outcome):
    assert brief_problems(brief(done_when=outcome), "kira", WORKFLOWS) == []


def test_lucas_numbered_words_and_fenced_lines_are_not_dictated_steps():
    words = "> 1. No need to clone, it's on the disk already.\n> 2. I need info."
    assert brief_problems(brief(words=words), "kira", WORKFLOWS) == []
    nested = "````\n```\n1. sample output\n```\n````\n- Rehearsal evidence exists"
    assert brief_problems(brief(done_when=nested), "kira", WORKFLOWS) == []


def test_a_brief_missing_a_template_heading_or_the_remote_contract_is_refused():
    without_goal = brief().replace("## Goal", "## Background")
    problems = brief_problems(without_goal, None, WORKFLOWS)
    assert any("missing or out of order: Goal" in problem for problem in problems)
    for host in ("fuji", "kir"):
        assert brief_problems(brief(), host, WORKFLOWS) == [
            f"the Contract section must show the session `--reply-host {host}`"
        ]


@pytest.mark.parametrize("context", ["", "```\nprivate\n```"])
def test_a_brief_without_context_for_the_session_is_refused(context):
    assert brief_problems(brief(context=context), "kira", WORKFLOWS) == [
        "the Context section must say whose work this is, where its results may be "
        "published, and which requirements are hard and which are open"
    ]
    no_heading = brief().replace("## Context", "## Background")
    assert any(
        "Context" in problem
        for problem in brief_problems(no_heading, "kira", WORKFLOWS)
    )


@given(kind=st.sampled_from(["None", "Design"]), reason=ONE_LINE_REASONS)
def test_a_brief_declaring_discovery_or_a_designed_process_is_not_forced_into_a_workflow(
    kind, reason
):
    assert brief_problems(brief(process=f"{kind}: {reason}"), "kira", WORKFLOWS) == []
    assert brief_problems(brief(process=f"{kind}: {reason}"), "kira", {}) == []


@given(command=st.sampled_from(sorted(WORKFLOWS)), wrapper=st.sampled_from(["", "`"]))
def test_a_brief_naming_an_installed_workflow_passes(command, wrapper):
    process = f"Workflow: {wrapper}{command}{wrapper} over the failing test"
    assert brief_problems(brief(process=process), "kira", WORKFLOWS) == []


@given(command=COMMAND_NAMES.filter(lambda name: name not in WORKFLOWS))
def test_a_brief_naming_a_workflow_that_is_not_installed_is_refused_with_the_installed_ones(
    command,
):
    problems = brief_problems(brief(process=f"Workflow: {command}"), "kira", WORKFLOWS)
    assert len(problems) == 1
    assert f"`{command}`, which is not an installed workflow" in problems[0]
    assert all(installed in problems[0] for installed in WORKFLOWS)


@pytest.mark.parametrize(
    "process",
    [
        "",
        "The session decides how to work.",
        "None:",
        "none: lowercase key",
        "Workflow: dotfiles-fix-loop\nNone: and also discovery",
        "```\nNone: hidden in a fence\n```",
    ],
)
def test_a_brief_without_exactly_one_process_declaration_is_refused(process):
    problems = brief_problems(brief(process=process), "kira", WORKFLOWS)
    assert len(problems) == 1
    assert "the Process section must hold one line" in problems[0]
    assert all(installed in problems[0] for installed in WORKFLOWS)


def test_a_brief_without_the_process_heading_is_told_the_declaration_it_owes():
    without_process = brief().replace("## Process", "## Approach")
    problems = brief_problems(without_process, "kira", {})
    assert any("missing or out of order: Process" in problem for problem in problems)
    assert any(
        "no workflow command is installed on this machine" in problem
        for problem in problems
    )
