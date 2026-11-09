import json

import pytest
from orchestration_test_support import run_orchestrator
from orchestrator_cli.session_messages import cli as session_message_cli
from session_message_test_support import brief


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
    assert "line 13 orders steps" in capsys.readouterr().err
    assert notifications == [] and copied_briefs == []


def file_remote_report(monkeypatch, reports):
    monkeypatch.delenv("HERDR_PANE_ID", raising=False)
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


def copy_report(reports, source, **fields):
    record = {**json.loads((reports / f"{source}.json").read_text()), **fields}
    (reports / f"{record['name']}.json").write_text(json.dumps(record))


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


def test_relay_prefers_an_exact_session_and_refuses_an_ambiguous_one(
    monkeypatch, tmp_path, capsys, notifications
):
    file_remote_report(monkeypatch, tmp_path)
    local = {"requester_pane": "wW:pQN", "requester_host": None}
    copy_report(tmp_path, "Mozart", name="Mozart-wW-pQN", **local)
    assert relay(monkeypatch, tmp_path, "Mozart", "--status-check") == 0
    assert notifications[-1][0] == "kira:Mozart"
    assert relay(monkeypatch, tmp_path, "wW:pQN", "--status-check") == 0
    assert notifications[-1][0] == "wW:pQN"
    copy_report(tmp_path, "Mozart", name="Mozart-kira")
    (tmp_path / "Mozart.json").unlink()
    assert relay(monkeypatch, tmp_path, "Mozart", "--status-check") == 1
    assert "Mozart matches several sessions" in capsys.readouterr().err
    assert len(notifications) == 2


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
