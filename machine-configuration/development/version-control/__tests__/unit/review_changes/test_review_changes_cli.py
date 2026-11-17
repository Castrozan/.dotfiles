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
    review_changes_cli.prompt_for_target([])
    assert prompt_doubles == ["MR/PR number, link or branch in group/project [main]: "]


def test_prompt_offers_the_request_detected_in_the_agent_reply(prompt_doubles, capsys):
    detected_request = RequestLink(ForgeRepository("gitlab.example", "team/app"), "9")
    review_changes_cli.prompt_for_target([detected_request])
    assert capsys.readouterr().out == ""
    assert prompt_doubles == [
        "MR/PR number, link or branch in group/project [team/app!9]: "
    ]


def test_prompt_lists_the_other_requests_a_number_can_pick(prompt_doubles, capsys):
    review_changes_cli.prompt_for_target(
        [
            RequestLink(ForgeRepository("gitlab.example", "team/app"), "9"),
            RequestLink(ForgeRepository("gitlab.example", "team/site"), "43"),
            RequestLink(ForgeRepository("github.com", "owner/host"), "530"),
        ]
    )
    assert capsys.readouterr().out == (
        "Also named by the agent, pick by number: team/site!43, owner/host#530\n"
    )
    assert prompt_doubles == [
        "MR/PR number, link or branch in group/project [team/app!9]: "
    ]


def test_typed_target_is_resolved_among_the_detected_requests(prompt_doubles):
    detected_requests = [
        RequestLink(ForgeRepository("gitlab.example", "team/site"), "43"),
        RequestLink(ForgeRepository("gitlab.example", "team/host"), "530"),
    ]
    with (
        patch(
            "review_changes_cli.latest_request_links_in_active_agent",
            return_value=detected_requests,
        ),
        patch("builtins.input", return_value="530"),
        patch("review_changes_cli.resolve_review_target") as resolve_review_target,
        patch("review_changes_cli.review_in_lazygit") as review_in_lazygit,
    ):
        review_changes_cli.review([])
    resolve_review_target.assert_called_once_with("530", detected_requests)
    review_in_lazygit.assert_called_once_with(resolve_review_target.return_value)


def test_command_line_target_skips_agent_reply_detection():
    with (
        patch(
            "review_changes_cli.latest_request_links_in_active_agent"
        ) as latest_request_links_in_active_agent,
        patch("review_changes_cli.resolve_review_target") as resolve_review_target,
        patch("review_changes_cli.review_in_lazygit"),
    ):
        review_changes_cli.review(["530"])
    latest_request_links_in_active_agent.assert_not_called()
    resolve_review_target.assert_called_once_with("530", [])


def test_prompt_outside_a_repository_names_no_repository(monkeypatch):
    prompts = []
    monkeypatch.setattr("builtins.input", lambda prompt: prompts.append(prompt) or "")
    monkeypatch.setattr(
        review_changes_cli, "origin_repository", lambda _directory: None
    )
    with patch("review_changes_cli.run_command", return_value=MagicMock(stdout="")):
        review_changes_cli.prompt_for_target([])
    assert prompts == ["MR/PR number, link or branch: "]
