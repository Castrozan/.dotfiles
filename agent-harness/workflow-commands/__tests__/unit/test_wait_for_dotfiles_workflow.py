import json

import pytest

import wait_for_dotfiles_workflow

RUN_IDENTIFIER = "wf_0bfbff58-962"


def write_state(projects_directory, status, result="# Report"):
    state_directory = projects_directory / "-checkout" / "session" / "workflows"
    state_directory.mkdir(parents=True, exist_ok=True)
    (state_directory / f"{RUN_IDENTIFIER}.json").write_text(
        json.dumps({"status": status, "result": result})
    )


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def test_returns_the_terminal_state_of_the_run(tmp_path):
    write_state(tmp_path, "completed")
    state = wait_for_dotfiles_workflow.wait_for_terminal_state(tmp_path, RUN_IDENTIFIER)
    assert wait_for_dotfiles_workflow.rendered_outcome(state) == (
        "status=completed\n# Report"
    )


def test_keeps_polling_a_running_run_until_its_wait_ceiling(tmp_path):
    write_state(tmp_path, "running")
    clock = FakeClock()
    state = wait_for_dotfiles_workflow.wait_for_terminal_state(
        tmp_path, RUN_IDENTIFIER, clock=clock, sleep=clock.sleep
    )
    assert state is None
    assert clock.now >= wait_for_dotfiles_workflow.MAXIMUM_WAIT_SECONDS
    assert wait_for_dotfiles_workflow.rendered_outcome(state) == (
        wait_for_dotfiles_workflow.STILL_RUNNING_MESSAGE
    )


def test_a_half_written_state_file_counts_as_still_running(tmp_path):
    write_state(tmp_path, "completed")
    next(tmp_path.glob("*/*/workflows/*.json")).write_text('{"status": "comp')
    assert (
        wait_for_dotfiles_workflow.terminal_workflow_state(tmp_path, RUN_IDENTIFIER)
        is None
    )


def test_a_structured_result_is_printed_as_json(tmp_path):
    write_state(tmp_path, "failed", result={"error": "aborted"})
    state = wait_for_dotfiles_workflow.terminal_workflow_state(tmp_path, RUN_IDENTIFIER)
    assert wait_for_dotfiles_workflow.rendered_outcome(state) == (
        'status=failed\n{"error": "aborted"}'
    )


def test_refuses_anything_but_a_run_identifier(monkeypatch):
    monkeypatch.setattr("sys.argv", ["dotfiles-workflow-wait", "../*"])
    with pytest.raises(SystemExit) as failure:
        wait_for_dotfiles_workflow.main()
    assert "not a workflow run ID" in str(failure.value)
