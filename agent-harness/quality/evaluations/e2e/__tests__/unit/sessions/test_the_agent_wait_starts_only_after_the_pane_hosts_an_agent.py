from e2e.sessions import e2e_herdr_io
from e2e.sessions.e2e_harness_profiles import CLAUDE_PROFILE


def stub_agent_registration_after(monkeypatch, polls_before_registration):
    polls = {"count": 0}
    events = []

    def pane_hosts_a_live_agent(pane_id):
        polls["count"] += 1
        return polls["count"] > polls_before_registration

    def wait_for_agent_status(pane_id, agent_status, timeout_seconds):
        events.append(("status", polls["count"] > polls_before_registration))
        return True

    monkeypatch.setattr(
        e2e_herdr_io, "pane_hosts_a_live_agent", pane_hosts_a_live_agent
    )
    monkeypatch.setattr(e2e_herdr_io, "wait_for_agent_status", wait_for_agent_status)
    monkeypatch.setattr(
        e2e_herdr_io, "wait_for_startup_output_to_settle", lambda *arguments: True
    )
    monkeypatch.setattr(e2e_herdr_io, "RESPONSE_POLL_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(e2e_herdr_io, "INPUT_SETTLE_SECONDS", 0)
    return events


def test_the_idle_wait_runs_only_once_the_pane_hosts_an_agent(monkeypatch):
    events = stub_agent_registration_after(monkeypatch, polls_before_registration=3)

    assert e2e_herdr_io.wait_for_agent_to_become_ready("pane", CLAUDE_PROFILE)
    assert events == [("status", True)]


def test_a_pane_that_never_hosts_an_agent_is_not_ready(monkeypatch):
    events = stub_agent_registration_after(monkeypatch, polls_before_registration=10**9)

    assert not e2e_herdr_io.wait_for_agent_to_become_ready(
        "pane", CLAUDE_PROFILE, timeout_seconds=0
    )
    assert events == []
