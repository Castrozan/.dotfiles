import signal
import subprocess
from unittest.mock import Mock

import pytest

import shorts_runner
from shorts_store import read_document, write_document


@pytest.fixture
def production_run(tmp_path, monkeypatch):
    directory = tmp_path / "runs" / "morning"
    directory.mkdir(parents=True)
    write_document(directory / "status.json", {"status": "started"})
    monkeypatch.setattr(shorts_runner, "publisher_readiness", lambda *arguments: None)
    monkeypatch.setattr(
        shorts_runner,
        "claim_slot",
        lambda *arguments: shorts_runner.SlotClaim(directory, None),
    )
    pages = Mock()
    monkeypatch.setattr(shorts_runner, "browser_pages", lambda *arguments: pages)
    monkeypatch.setattr(shorts_runner, "agent_arguments", lambda *arguments: [])
    process = Mock(pid=12345)
    process.wait.return_value = 0
    monkeypatch.setattr(shorts_runner.subprocess, "Popen", Mock(return_value=process))
    monkeypatch.setattr(shorts_runner.os, "killpg", Mock())
    return directory, pages, process


@pytest.mark.parametrize("outcome", ["success", "hold", "timeout", "interrupt"])
def test_browser_pages_are_cleaned_after_every_agent_outcome(
    tmp_path, monkeypatch, production_run, outcome
):
    directory, pages, process = production_run
    if outcome == "hold":
        write_document(directory / "hold.json", {"reason": "quality gate failed"})
    if outcome == "timeout":
        process.wait.side_effect = [subprocess.TimeoutExpired("codex", 7200), 0]
    if outcome == "interrupt":
        process.wait.side_effect = [SystemExit(128 + signal.SIGTERM), 0]
        with pytest.raises(SystemExit):
            shorts_runner.start_run(tmp_path, 9, {})
    else:
        result = shorts_runner.start_run(tmp_path, 9, {})
        assert (
            result["status"]
            == {
                "success": "agent_finished",
                "hold": "held",
                "timeout": "needs_inspection",
            }[outcome]
        )
    pages.begin.assert_called_once()
    pages.cleanup.assert_called_once()
    assert signal.getsignal(signal.SIGTERM) != shorts_runner.terminate_run


def test_cleanup_error_is_recorded_for_inspection(tmp_path, production_run):
    directory, pages, process = production_run
    pages.cleanup.side_effect = ValueError("browser unavailable")
    result = shorts_runner.start_run(tmp_path, 9, {})
    assert result["browser_cleanup"] == "needs_inspection"
    assert read_document(directory / "browser-cleanup.json") == {
        "status": "needs_inspection",
        "reason": "browser unavailable",
    }


def test_failed_page_initialization_cleans_up_without_spending_a_session(
    tmp_path, production_run
):
    directory, pages, process = production_run
    pages.begin.side_effect = ValueError("leftovers could not be closed")
    with pytest.raises(ValueError, match="leftovers"):
        shorts_runner.start_run(tmp_path, 9, {})
    pages.cleanup.assert_called_once()
    shorts_runner.subprocess.Popen.assert_not_called()
    assert read_document(directory / "status.json")["status"] == "needs_inspection"
