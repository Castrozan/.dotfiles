import subprocess
from types import SimpleNamespace
from unittest.mock import patch

import dotfiles_ci


def completed_run(workflow_name, conclusion):
    return {
        "workflowName": workflow_name,
        "status": "completed",
        "conclusion": conclusion,
        "url": f"https://github.com/owner/repo/actions/runs/{workflow_name}",
    }


def in_progress_run(workflow_name):
    return {
        "workflowName": workflow_name,
        "status": "in_progress",
        "conclusion": None,
        "url": f"https://github.com/owner/repo/actions/runs/{workflow_name}",
    }


def run_main_against(run_batches):
    with patch("dotfiles_ci.resolve_commit_sha", return_value="deadbeef"):
        with patch("dotfiles_ci.fetch_runs_for_commit", side_effect=run_batches):
            with patch("dotfiles_ci.time.sleep"):
                with patch("dotfiles_ci.sys.argv", ["dotfiles-ci"]):
                    return dotfiles_ci.main()


class TestVerdict:
    def test_green_ci_exits_zero(self):
        batches = [
            [completed_run("tests", "success"), completed_run("lint", "success")]
        ]
        assert run_main_against(batches) == 0

    def test_a_failed_run_exits_red(self):
        batches = [
            [completed_run("tests", "failure"), completed_run("lint", "success")]
        ]
        assert run_main_against(batches) == dotfiles_ci.EXIT_CODE_CI_IS_RED

    def test_a_cancelled_run_counts_as_a_failure(self):
        batches = [[completed_run("tests", "cancelled")]]
        assert run_main_against(batches) == dotfiles_ci.EXIT_CODE_CI_IS_RED

    def test_a_skipped_run_does_not_count_as_a_failure(self):
        batches = [[completed_run("deploy reports", "skipped")]]
        assert run_main_against(batches) == 0


class TestWaiting:
    def test_it_polls_until_every_run_completes(self):
        batches = [
            [in_progress_run("tests")],
            [in_progress_run("tests")],
            [completed_run("tests", "success")],
        ]
        assert run_main_against(batches) == 0

    def test_a_commit_with_no_registered_run_is_loud_not_green(self):
        batches = [[] for _ in range(dotfiles_ci.POLLS_WAITING_FOR_RUNS_TO_APPEAR)]
        assert run_main_against(batches) == dotfiles_ci.EXIT_CODE_CI_VERDICT_UNKNOWN

    def test_runs_still_going_past_the_budget_leave_the_verdict_unknown(self):
        batches = [[in_progress_run("tests")]] * (
            dotfiles_ci.POLLS_WAITING_FOR_RUNS_TO_COMPLETE + 1
        )
        assert run_main_against(batches) == dotfiles_ci.EXIT_CODE_CI_VERDICT_UNKNOWN

    def test_the_completion_wait_stays_under_ten_minutes(self):
        budget_seconds = (
            dotfiles_ci.POLLS_WAITING_FOR_RUNS_TO_COMPLETE
            * dotfiles_ci.SECONDS_BETWEEN_POLLS
        )
        assert budget_seconds <= 600


class TestTheRepositoryIsPinnedRatherThanInheritedFromTheCaller:
    def test_the_commit_is_resolved_inside_the_dotfiles_checkout(self):
        with patch("dotfiles_ci.subprocess.run") as subprocess_run:
            subprocess_run.return_value = SimpleNamespace(stdout="deadbeef\n")
            dotfiles_ci.resolve_commit_sha("HEAD")
        assert subprocess_run.call_args.kwargs["cwd"] == dotfiles_ci.DOTFILES_DIRECTORY

    def test_the_runs_are_queried_inside_the_dotfiles_checkout(self):
        with patch("dotfiles_ci.subprocess.run") as subprocess_run:
            subprocess_run.return_value = SimpleNamespace(stdout="[]")
            dotfiles_ci.fetch_runs_for_commit("deadbeef")
        assert subprocess_run.call_args.kwargs["cwd"] == dotfiles_ci.DOTFILES_DIRECTORY

    def test_an_unresolvable_reference_is_unknown_rather_than_red(self):
        unresolvable = subprocess.CalledProcessError(128, ["git", "rev-parse"])
        with patch("dotfiles_ci.resolve_commit_sha", side_effect=unresolvable):
            with patch("dotfiles_ci.sys.argv", ["dotfiles-ci", "not-a-revision"]):
                assert dotfiles_ci.main() == dotfiles_ci.EXIT_CODE_CI_VERDICT_UNKNOWN


class TestReporting:
    def test_each_run_reports_its_outcome_and_url(self, capsys):
        dotfiles_ci.report_runs([completed_run("tests", "failure")])
        printed = capsys.readouterr().out
        assert "failure" in printed
        assert "tests" in printed
        assert "https://github.com/owner/repo/actions/runs/tests" in printed

    def test_an_incomplete_run_reports_its_status_instead_of_a_blank(self):
        assert "in_progress" in dotfiles_ci.describe_run(in_progress_run("tests"))
