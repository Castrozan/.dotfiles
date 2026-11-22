import asyncio
import time

import agent_route
from a2a_fakes import install_a2a, pane_reports, sent_arguments
from agent_route import ask_agent, spoken_answer, tagged_answer
from conversation_addressee import Addressee
from hypothesis import given
from hypothesis import strategies as st

HOLDER = Addressee("wW:pQZ", "Suzuka", 0)
SPOKEN_TEXT = st.text(
    st.characters(blacklist_categories=("Cc", "Cs", "Zl", "Zp")), min_size=1
).filter(str.strip)


def reports_for(request="is my repo clean?", number=1):
    async def collect():
        return [report async for report in ask_agent(HOLDER, request, number)]

    return asyncio.run(collect())


def texts_and_finality(reports):
    return [(report.text, report.final) for report in reports]


def test_the_spoken_answer_is_the_agents_last_marked_line():
    output = "⏺ Bash(nproc)\n  12\n⏺ This machine has 12 cores.\n"
    assert spoken_answer(output) == (
        "This machine has 12 cores.",
        "⏺ This machine has 12 cores.",
    )


@given(answer=SPOKEN_TEXT, marker=st.sampled_from(["", "⏺ ", "• ", "▣ "]))
def test_a_line_opening_with_the_tag_is_the_answer_under_any_harness_marker(
    answer, marker
):
    output = f"⏺ Bash(git status)\n{marker}LIVE-ANSWER-3: {answer}\n⏺ Next step"
    assert tagged_answer(output, "LIVE-ANSWER-3") == answer.strip()


@given(request=SPOKEN_TEXT, number=st.integers(min_value=1, max_value=999))
def test_the_brief_itself_never_reads_as_an_answer(request, number):
    tag = agent_route.answer_tag(number)
    brief = agent_route.BRIEF.format(request=request, tag=tag)
    assert tagged_answer(brief, tag) is None


def test_another_requests_answer_is_not_taken_for_this_one():
    output = "⏺ LIVE-ANSWER-12: The disk is fine."
    assert tagged_answer(output, "LIVE-ANSWER-1") is None


def test_the_task_reaches_the_named_pane_with_its_answer_tag(tmp_path, monkeypatch):
    install_a2a(tmp_path, monkeypatch)
    pane_reports(tmp_path, "completed", "⏺ LIVE-ANSWER-4: Main is clean.")
    reports_for(number=4)
    arguments = sent_arguments(tmp_path)
    assert arguments[:4] == ["send", "--sender", agent_route.SENDER, "wW:pQZ"]
    assert "is my repo clean?" in arguments[4]
    assert "LIVE-ANSWER-4 and a colon" in arguments[4]


def test_an_idle_agent_answer_comes_back_when_its_turn_ends(tmp_path, monkeypatch):
    install_a2a(tmp_path, monkeypatch)
    pane_reports(tmp_path, "completed", "⏺ Bash(git status)\n⏺ Main is clean.")
    assert texts_and_finality(reports_for()) == [("Main is clean.", True)]


def test_a_busy_agent_answer_comes_back_while_its_turn_still_runs(
    tmp_path, monkeypatch
):
    install_a2a(tmp_path, monkeypatch)
    monkeypatch.setattr(agent_route, "ANSWER_DEADLINE_SECONDS", 30)
    pane_reports(tmp_path, "working", "⏺ Agent(build)\n⏺ LIVE-ANSWER-1: Sim, chegou.")
    started = time.monotonic()
    assert texts_and_finality(reports_for()) == [("Sim, chegou.", True)]
    assert time.monotonic() - started < 5


def test_an_agent_that_never_answers_is_reported_still_working_then_timed_out(
    tmp_path, monkeypatch
):
    install_a2a(tmp_path, monkeypatch)
    pane_reports(tmp_path, "working", "⏺ Agent(build)")
    reports = reports_for()
    assert (agent_route.STILL_WORKING, False) in texts_and_finality(reports)
    assert texts_and_finality(reports)[-1] == (agent_route.NO_ANSWER_IN_TIME, True)
    assert [report.final for report in reports].count(True) == 1
    assert reports[-1].seconds < 1 + agent_route.COMMAND_TIMEOUT_SECONDS


def test_a_hung_a2a_status_is_cut_off_and_still_times_out(tmp_path, monkeypatch):
    install_a2a(tmp_path, monkeypatch, status="exec sleep 7")
    monkeypatch.setattr(agent_route, "COMMAND_TIMEOUT_SECONDS", 0.3)
    reports = reports_for()
    assert texts_and_finality(reports)[-1] == (agent_route.NO_ANSWER_IN_TIME, True)
    assert reports[-1].seconds < 3


def test_a_refused_task_is_spoken_as_a_failure(tmp_path, monkeypatch):
    install_a2a(tmp_path, monkeypatch, send="echo 'a2a: peer refused the task'; exit 1")
    assert texts_and_finality(reports_for()) == [
        ("The agent could not finish that: a2a: peer refused the task", True)
    ]


def test_a_task_whose_pane_vanished_is_spoken_as_a_failure(tmp_path, monkeypatch):
    install_a2a(tmp_path, monkeypatch)
    (tmp_path / "task").write_text(
        '{"state": "failed", "output": "", "errorMessage": "the pane is gone"}'
    )
    assert texts_and_finality(reports_for()) == [
        ("The agent could not finish that: the pane is gone", True)
    ]
