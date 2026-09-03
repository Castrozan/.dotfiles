import json
import socket
from unittest.mock import patch

import nightly_deep_test_tiers
import pytest


@pytest.fixture(autouse=True)
def keep_the_log_and_the_steward_inbox_off_the_live_machine(tmp_path, monkeypatch):
    monkeypatch.setattr(
        nightly_deep_test_tiers, "LOG_DIRECTORY", tmp_path / "nightly-log"
    )
    monkeypatch.setenv("STEWARD_WORKSPACE_DIR", str(tmp_path / "no-steward-here"))


class TestIdleWindow:
    def test_three_in_the_morning_is_inside_the_window(self):
        assert nightly_deep_test_tiers.is_inside_the_idle_window(3)

    def test_the_middle_of_a_working_day_is_outside_the_window(self):
        assert not nightly_deep_test_tiers.is_inside_the_idle_window(14)

    def test_a_run_outside_the_window_does_nothing_and_stays_green(self):
        with patch("nightly_deep_test_tiers.current_hour", return_value=14):
            with patch("nightly_deep_test_tiers.sys.argv", ["nightly"]):
                with patch(
                    "nightly_deep_test_tiers.run_the_deep_tiers_and_clean_up"
                ) as tiers:
                    assert nightly_deep_test_tiers.main() == 0
                    tiers.assert_not_called()

    def test_force_runs_the_tiers_outside_the_window(self):
        with patch("nightly_deep_test_tiers.current_hour", return_value=14):
            with patch("nightly_deep_test_tiers.sys.argv", ["nightly", "--force"]):
                with patch("nightly_deep_test_tiers.shutil.which", return_value="/x"):
                    with patch(
                        "nightly_deep_test_tiers.run_the_deep_tiers_and_clean_up",
                        return_value=0,
                    ) as tiers:
                        assert nightly_deep_test_tiers.main() == 0
                        tiers.assert_called_once()

    def test_a_missing_runner_fails_loudly_instead_of_reporting_green(self):
        with patch("nightly_deep_test_tiers.current_hour", return_value=3):
            with patch("nightly_deep_test_tiers.sys.argv", ["nightly"]):
                with patch("nightly_deep_test_tiers.shutil.which", return_value=None):
                    assert (
                        nightly_deep_test_tiers.main()
                        == nightly_deep_test_tiers.EXIT_CODE_CANNOT_RUN
                    )

    def test_a_missing_runner_leaves_a_failed_verdict_in_the_log(self):
        with patch("nightly_deep_test_tiers.current_hour", return_value=3):
            with patch("nightly_deep_test_tiers.sys.argv", ["nightly"]):
                with patch("nightly_deep_test_tiers.shutil.which", return_value=None):
                    nightly_deep_test_tiers.main()
        verdict = nightly_deep_test_tiers.log_file_path().read_text().splitlines()[-1]
        assert verdict == nightly_deep_test_tiers.CANNOT_RUN_VERDICT
        assert verdict.startswith("FAILED")


class TestEveryTierRuns:
    def test_a_failing_tier_does_not_stop_the_next_one(self, tmp_path):
        log = (tmp_path / "log").open("w")
        with patch("nightly_deep_test_tiers.run_tier", side_effect=[1, 0]) as tier:
            failed = nightly_deep_test_tiers.run_every_tier_reporting_all_failures(log)
        log.close()

        assert tier.call_count == len(nightly_deep_test_tiers.DEEP_TIER_FLAGS)
        assert failed == ["--integration-scripts"]

    def test_the_tiers_it_owns_are_the_ones_ci_cannot_reach(self):
        assert nightly_deep_test_tiers.DEEP_TIER_FLAGS == (
            "--integration-scripts",
            "--runtime",
        )


class TestArtifactCleanup:
    def test_it_finds_cache_directories_and_ignores_source_trees(self, tmp_path):
        (tmp_path / "home" / "base").mkdir(parents=True)
        (tmp_path / "home" / "base" / ".pytest_cache").mkdir()
        (tmp_path / "home" / "base" / "__pycache__").mkdir()
        (tmp_path / "home" / "base" / "scripts").mkdir()

        found = {
            path.name
            for path in nightly_deep_test_tiers.artifact_directories_under(tmp_path)
        }

        assert found == {".pytest_cache", "__pycache__"}

    def test_it_never_walks_into_git_or_sibling_worktrees(self, tmp_path):
        (tmp_path / ".git" / ".pytest_cache").mkdir(parents=True)
        (tmp_path / ".worktrees" / "other" / ".ruff_cache").mkdir(parents=True)

        assert nightly_deep_test_tiers.artifact_directories_under(tmp_path) == []

    def test_the_child_environment_writes_no_cache(self):
        environment = nightly_deep_test_tiers.environment_that_leaves_no_cache()

        assert environment["PYTHONDONTWRITEBYTECODE"] == "1"
        assert "no:cacheprovider" in environment["PYTEST_ADDOPTS"]


class TestAFailedNightReachesTheSteward:
    @pytest.fixture(autouse=True)
    def a_steward_workspace(self, tmp_path, monkeypatch):
        self.steward_workspace = tmp_path / "steward"
        self.steward_workspace.mkdir()
        monkeypatch.setenv("STEWARD_WORKSPACE_DIR", str(self.steward_workspace))

    def run_the_night_with_tiers_failing(self, failed_tiers):
        with patch(
            "nightly_deep_test_tiers.run_every_tier_reporting_all_failures",
            return_value=failed_tiers,
        ):
            with patch(
                "nightly_deep_test_tiers.untracked_paths_in_repository",
                return_value=set(),
            ):
                with patch(
                    "nightly_deep_test_tiers.remove_generated_cache_directories"
                ):
                    with patch(
                        "nightly_deep_test_tiers.prune_docker_build_leftovers_the_run_did_not_reuse"
                    ):
                        with patch(
                            "nightly_deep_test_tiers.report_paths_the_run_left_behind"
                        ):
                            return nightly_deep_test_tiers.run_the_deep_tiers_and_clean_up()

    def inbox_messages(self):
        inbox = self.steward_workspace / "inbox"
        return sorted(inbox.glob("*.json")) if inbox.is_dir() else []

    def test_a_failed_tier_leaves_a_message_the_steward_tick_drains(self):
        assert self.run_the_night_with_tiers_failing(["--runtime"]) == 1
        [message_file] = self.inbox_messages()
        assert message_file.name.endswith("-from-nightly-deep-tiers.json")
        message = json.loads(message_file.read_text())
        assert message["from"] == "nightly-deep-tiers"
        assert message["to"] == "steward"
        assert isinstance(message["sent_unix"], int)
        assert "FAILED tiers: --runtime" in message["text"]
        assert socket.gethostname() in message["text"]
        assert str(nightly_deep_test_tiers.log_file_path()) in message["text"]

    def test_the_verdict_stays_the_last_log_line(self):
        self.run_the_night_with_tiers_failing(["--runtime"])
        lines = nightly_deep_test_tiers.log_file_path().read_text().splitlines()
        assert lines[-1] == "FAILED tiers: --runtime"
        assert any(
            "left the failed night in the steward inbox" in line for line in lines
        )

    def test_a_passing_night_leaves_no_message(self):
        assert self.run_the_night_with_tiers_failing([]) == 0
        assert self.inbox_messages() == []

    def test_a_night_that_cannot_run_leaves_a_message(self):
        with patch("nightly_deep_test_tiers.current_hour", return_value=3):
            with patch("nightly_deep_test_tiers.sys.argv", ["nightly"]):
                with patch("nightly_deep_test_tiers.shutil.which", return_value=None):
                    nightly_deep_test_tiers.main()
        [message_file] = self.inbox_messages()
        assert (
            nightly_deep_test_tiers.CANNOT_RUN_VERDICT
            in json.loads(message_file.read_text())["text"]
        )

    def test_a_machine_without_a_steward_only_logs_it(self, monkeypatch, tmp_path):
        monkeypatch.setenv("STEWARD_WORKSPACE_DIR", str(tmp_path / "absent"))
        assert self.run_the_night_with_tiers_failing(["--runtime"]) == 1
        assert not (tmp_path / "absent").exists()
        assert "nobody is told" in nightly_deep_test_tiers.log_file_path().read_text()
