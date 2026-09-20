import json
import socket
from unittest.mock import patch

import nightly_deep_test_tiers
import pytest


class TestAFailedNightReachesTheSteward:
    @pytest.fixture(autouse=True)
    def a_steward_workspace(
        self,
        keep_the_log_and_the_steward_inbox_off_the_live_machine,
        tmp_path,
        monkeypatch,
    ):
        self.steward_workspace = tmp_path / "steward"
        self.steward_workspace.mkdir()
        monkeypatch.setenv("STEWARD_WORKSPACE_DIR", str(self.steward_workspace))

    def run_the_night_with_tiers_failing(self, failed_tiers, skipped_tiers=()):
        with patch(
            "nightly_deep_test_tiers.run_every_tier_reporting_all_failures",
            return_value=(failed_tiers, list(skipped_tiers)),
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
