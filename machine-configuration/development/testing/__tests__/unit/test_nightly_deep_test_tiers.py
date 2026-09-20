from unittest.mock import patch

import nightly_cleanup
import nightly_deep_test_tiers
import pytest

pytestmark = pytest.mark.usefixtures(
    "keep_the_log_and_the_steward_inbox_off_the_live_machine"
)


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
        with patch(
            "nightly_deep_test_tiers.run_tier", side_effect=[1, 0, 0, 0, 0]
        ) as tier:
            failed, skipped = (
                nightly_deep_test_tiers.run_every_tier_reporting_all_failures(log)
            )
        log.close()

        assert tier.call_count == len(nightly_deep_test_tiers.DEEP_TIER_FLAGS)
        assert failed == ["--integration-scripts"]
        assert skipped == []

    def test_a_skipped_tier_is_neither_a_pass_nor_a_failure(self, tmp_path):
        log = (tmp_path / "log").open("w")
        skip = nightly_deep_test_tiers.TIER_SKIPPED_STATUS
        with patch(
            "nightly_deep_test_tiers.run_tier", side_effect=[0, 0, 0, skip, skip]
        ):
            failed, skipped = (
                nightly_deep_test_tiers.run_every_tier_reporting_all_failures(log)
            )
        log.close()

        assert failed == []
        assert skipped == ["--integration", "--e2e"]

    def test_the_tiers_it_owns_are_the_ones_ci_cannot_reach(self):
        assert nightly_deep_test_tiers.DEEP_TIER_FLAGS == (
            "--integration-scripts",
            "--runtime",
            "--perf",
            "--integration",
            "--e2e",
        )


class TestArtifactCleanup:
    def test_it_finds_cache_directories_and_ignores_source_trees(self, tmp_path):
        (tmp_path / "home" / "base").mkdir(parents=True)
        (tmp_path / "home" / "base" / ".pytest_cache").mkdir()
        (tmp_path / "home" / "base" / "__pycache__").mkdir()
        (tmp_path / "home" / "base" / "scripts").mkdir()

        found = {
            path.name for path in nightly_cleanup.artifact_directories_under(tmp_path)
        }

        assert found == {".pytest_cache", "__pycache__"}

    def test_it_never_walks_into_git_or_sibling_worktrees(self, tmp_path):
        (tmp_path / ".git" / ".pytest_cache").mkdir(parents=True)
        (tmp_path / ".worktrees" / "other" / ".ruff_cache").mkdir(parents=True)

        assert nightly_cleanup.artifact_directories_under(tmp_path) == []

    def test_the_child_environment_writes_no_cache(self):
        environment = nightly_deep_test_tiers.environment_that_leaves_no_cache()

        assert environment["PYTHONDONTWRITEBYTECODE"] == "1"
        assert "no:cacheprovider" in environment["PYTEST_ADDOPTS"]


class TestTheVerdictSeparatesSkippedFromPassed:
    def test_a_skipped_tier_is_named_as_proving_nothing(self):
        verdict = nightly_deep_test_tiers.night_verdict([], ["--e2e"])
        assert "SKIPPED, proving nothing: --e2e" in verdict
        assert "--e2e" not in verdict.split(". SKIPPED")[0]

    def test_a_night_where_every_tier_skipped_is_a_failure(self):
        verdict = nightly_deep_test_tiers.night_verdict(
            [], list(nightly_deep_test_tiers.DEEP_TIER_FLAGS)
        )
        assert verdict.startswith("FAILED")

    def test_a_failure_outranks_a_skip_in_the_verdict(self):
        verdict = nightly_deep_test_tiers.night_verdict(["--perf"], ["--e2e"])
        assert verdict.startswith("FAILED tiers: --perf")
        assert "SKIPPED, proving nothing: --e2e" in verdict
