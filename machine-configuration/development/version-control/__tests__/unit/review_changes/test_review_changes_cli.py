import signal
from unittest.mock import MagicMock, patch

import pytest

import review_changes_cli
from request_links import ForgeRepository, RequestLink


@pytest.fixture
def restored_signal_handlers():
    original_handlers = {
        terminating_signal: signal.getsignal(terminating_signal)
        for terminating_signal in (signal.SIGHUP, signal.SIGTERM)
    }
    yield
    for terminating_signal, handler in original_handlers.items():
        signal.signal(terminating_signal, handler)


@pytest.mark.parametrize("terminating_signal", [signal.SIGHUP, signal.SIGTERM])
def test_closing_the_review_pane_unwinds_through_cleanup(
    restored_signal_handlers, terminating_signal
):
    review_changes_cli.route_terminating_signals_through_cleanup()
    handler = signal.getsignal(terminating_signal)
    with pytest.raises(SystemExit) as exit_information:
        handler(terminating_signal, None)
    assert exit_information.value.code == 128 + terminating_signal


def test_signals_after_the_first_cannot_interrupt_cleanup(restored_signal_handlers):
    review_changes_cli.route_terminating_signals_through_cleanup()
    with pytest.raises(SystemExit):
        signal.getsignal(signal.SIGHUP)(signal.SIGHUP, None)
    assert signal.getsignal(signal.SIGHUP) is signal.SIG_IGN
    assert signal.getsignal(signal.SIGTERM) is signal.SIG_IGN


@pytest.fixture
def prompt_doubles(monkeypatch):
    prompts = []
    monkeypatch.setattr("builtins.input", lambda prompt: prompts.append(prompt) or "")
    monkeypatch.setattr(
        review_changes_cli,
        "origin_repository",
        lambda _directory: ForgeRepository("github.com", "group/project"),
    )
    with patch(
        "review_changes_cli.run_command", return_value=MagicMock(stdout="main\n")
    ):
        yield prompts


def test_prompt_names_the_repository_a_bare_number_resolves_in(prompt_doubles):
    review_changes_cli.prompt_for_target(None)
    assert prompt_doubles == ["MR/PR number, link or branch in group/project [main]: "]


def test_prompt_offers_the_request_detected_in_the_agent_reply(prompt_doubles):
    detected_request = RequestLink(ForgeRepository("gitlab.example", "team/app"), "9")
    review_changes_cli.prompt_for_target(detected_request)
    assert prompt_doubles == [
        "MR/PR number, link or branch in group/project [team/app!9]: "
    ]


def test_prompt_outside_a_repository_names_no_repository(monkeypatch):
    prompts = []
    monkeypatch.setattr("builtins.input", lambda prompt: prompts.append(prompt) or "")
    monkeypatch.setattr(
        review_changes_cli, "origin_repository", lambda _directory: None
    )
    with patch("review_changes_cli.run_command", return_value=MagicMock(stdout="")):
        review_changes_cli.prompt_for_target(None)
    assert prompts == ["MR/PR number, link or branch: "]
