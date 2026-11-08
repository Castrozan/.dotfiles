import json

import pytest
from orchestration_test_support import run_orchestrator
from orchestrator_cli.session_messages import cli as session_message_cli
from orchestrator_cli.session_messages.brief_template import brief_problems

CONTRACT = """## Contract

```
ssh chise orchestrator decision file --to Ibaraki --sender Mozart --reply-host kira
ssh chise orchestrator report file --to Ibaraki --sender Mozart --reply-host kira
```
"""


def brief(done_when="- Rehearsal evidence comes from GitLab on the VPN", words=""):
    return f"""# Brief: GitLab evidence for the rehearsal

## Goal

The rehearsal reads the work GitLab without glab inside its sandbox.

## Done when

{done_when}

## Constraints

- Leave the VPN as Lucas set it.

## Workspace and worktree

kira, `~/clawde`.

## Lucas's words

> a script outside the sandbox fetches GitLab (safe)
{words}

{CONTRACT}"""


def test_a_brief_stating_outcomes_passes_and_one_dictating_steps_is_refused():
    assert brief_problems(brief(), "kira") == []
    numbered = "1. Build the gate script\n2. Deny glab\n3. Rehearse, then disconnect"
    problems = brief_problems(brief(done_when=numbered), "kira")
    assert len(problems) == 3
    assert all("orders steps" in problem for problem in problems)
    inline = "- Build it: 1) the gate script; 2) deny glab"
    assert len(brief_problems(brief(done_when=inline), "kira")) == 1


def test_lucas_numbered_words_and_fenced_lines_are_not_dictated_steps():
    words = "> 1. No need to clone, it's on the disk already.\n> 2. I need info."
    assert brief_problems(brief(words=words), "kira") == []


def test_a_brief_missing_a_template_heading_or_the_remote_contract_is_refused():
    without_goal = brief().replace("## Goal", "## Background")
    problems = brief_problems(without_goal, None)
    assert any("missing or out of order: Goal" in problem for problem in problems)
    assert brief_problems(brief(), "fuji") == [
        "the Contract section must show the session `--reply-host fuji`"
    ]


@pytest.fixture
def copied_briefs(monkeypatch):
    copied = []
    monkeypatch.setattr(
        session_message_cli,
        "copy_file_to_host",
        lambda path, host: copied.append((path, host)),
    )
    return copied


def dispatch(monkeypatch, tmp_path, text, *arguments):
    path = tmp_path / "brief.md"
    path.write_text(text)
    return run_orchestrator(
        monkeypatch,
        path,
        "Mozart",
        *arguments,
        command="dispatch",
        location_flag="--brief",
    )


def test_dispatch_copies_a_remote_brief_and_hands_it_over_without_steps(
    monkeypatch, tmp_path, notifications, copied_briefs
):
    assert dispatch(monkeypatch, tmp_path, brief(), "--host", "kira") == 0
    assert copied_briefs == [(tmp_path / "brief.md", "kira")]
    target, _, text = notifications[-1]
    assert target == "kira:Mozart"
    assert f"read {tmp_path / 'brief.md'} and carry it out. You plan the steps" in text


def test_dispatch_sends_nothing_when_the_brief_dictates_steps(
    monkeypatch, tmp_path, capsys, notifications, copied_briefs
):
    steps = brief(done_when="1. Build the gate script\n2. Rehearse")
    assert dispatch(monkeypatch, tmp_path, steps, "--host", "kira") == 1
    assert "line 9 orders steps" in capsys.readouterr().err
    assert notifications == [] and copied_briefs == []


def file_remote_report(monkeypatch, reports):
    monkeypatch.delenv("HERDR_PANE_ID")
    report = {
        "goal": "rehearsal reads GitLab",
        "state": "working",
        "done_check": "one rehearsal on the VPN",
        "progress": "gate script pushed",
        "next_step": "rehearse",
    }
    filing = ["file", "--to", "Ibaraki", "--sender", "Mozart", "--reply-host", "kira"]
    run_orchestrator(
        monkeypatch, reports, *filing, stdin_text=json.dumps(report), command="report"
    )


def relay(monkeypatch, reports, session, *content):
    return run_orchestrator(
        monkeypatch,
        reports,
        session,
        *content,
        command="relay",
        location_flag="--reports-dir",
    )


def test_relay_quotes_lucas_to_the_session_on_the_host_its_report_named(
    monkeypatch, tmp_path, notifications
):
    file_remote_report(monkeypatch, tmp_path)
    words = "vpn is already\nconnected"
    assert relay(monkeypatch, tmp_path, "Mozart", "--words", words) == 0
    assert notifications[-1][0] == "kira:Mozart"
    assert notifications[-1][2] == (
        'Lucas\'s words: "vpn is already connected". '
        "You decide what they change in your plan."
    )


def test_relay_refuses_a_fact_that_carries_a_plan(
    monkeypatch, tmp_path, capsys, notifications
):
    plan = "kira rebuilt. Now connect the VPN\nthen rehearse once and disconnect"
    assert relay(monkeypatch, tmp_path, "Mozart", "--fact", plan) == 1
    assert relay(monkeypatch, tmp_path, "Mozart", "--fact", "x" * 201) == 1
    assert "over its limit of 200" in capsys.readouterr().err
    assert notifications == []


def test_a_status_check_reaches_a_pane_that_never_reported(
    monkeypatch, tmp_path, notifications
):
    assert relay(monkeypatch, tmp_path, "wW:pRH", "--status-check") == 0
    target, _, text = notifications[-1]
    assert target == "wW:pRH"
    assert text.startswith("Status check:")
    assert "background commands are still alive" in text
