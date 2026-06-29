import chrome_version_detection
import drift_observation_state
import frontmost_application

MAIN_PROCESS_EXECUTABLE_PATH = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)
HELPER_PROCESS_EXECUTABLE_PATH = (
    "/Applications/Google Chrome.app/Contents/Frameworks/"
    "Google Chrome Framework.framework/Versions/149.0.7827.156/"
    "Helpers/Google Chrome Helper.app/Contents/MacOS/Google Chrome Helper"
)


class TestExtractChromeVersionFromVersionReport:
    def test_extracts_dotted_version(self):
        assert (
            chrome_version_detection.extract_chrome_version_from_version_report(
                "Google Chrome 149.0.7827.197 "
            )
            == "149.0.7827.197"
        )

    def test_returns_none_when_no_version(self):
        assert (
            chrome_version_detection.extract_chrome_version_from_version_report(
                "no version here"
            )
            is None
        )


class TestExtractFrameworkVersionFromExecutablePath:
    def test_extracts_version_from_helper_path(self):
        assert (
            chrome_version_detection.extract_framework_version_from_executable_path(
                HELPER_PROCESS_EXECUTABLE_PATH
            )
            == "149.0.7827.156"
        )

    def test_returns_none_for_main_process_path_without_version(self):
        assert (
            chrome_version_detection.extract_framework_version_from_executable_path(
                MAIN_PROCESS_EXECUTABLE_PATH
            )
            is None
        )


class TestRunningVersionsHaveDriftedFromOnDisk:
    def test_no_drift_when_no_running_versions(self):
        assert not chrome_version_detection.running_versions_have_drifted_from_on_disk(
            "149.0.7827.197", set()
        )

    def test_no_drift_when_running_matches_on_disk(self):
        assert not chrome_version_detection.running_versions_have_drifted_from_on_disk(
            "149.0.7827.197", {"149.0.7827.197"}
        )

    def test_drift_when_running_is_older(self):
        assert chrome_version_detection.running_versions_have_drifted_from_on_disk(
            "149.0.7827.197", {"149.0.7827.156"}
        )

    def test_drift_when_running_set_mixes_old_and_current(self):
        assert chrome_version_detection.running_versions_have_drifted_from_on_disk(
            "149.0.7827.197", {"149.0.7827.197", "149.0.7827.156"}
        )


class TestFrontmostNameReportIndicatesChrome:
    def test_true_for_chrome_display_name(self):
        assert frontmost_application.frontmost_name_report_indicates_chrome(
            '"LSDisplayName"="Google Chrome"'
        )

    def test_false_for_other_application(self):
        assert not frontmost_application.frontmost_name_report_indicates_chrome(
            '"LSDisplayName"="WezTerm"'
        )

    def test_false_for_chrome_helper_display_name(self):
        assert not frontmost_application.frontmost_name_report_indicates_chrome(
            '"LSDisplayName"="Google Chrome Helper"'
        )

    def test_false_for_empty_report(self):
        assert not frontmost_application.frontmost_name_report_indicates_chrome("")


class TestShouldRestartAfterObservation:
    def test_below_threshold_does_not_restart(self):
        assert not drift_observation_state.should_restart_after_observation(1, 2)

    def test_at_threshold_restarts(self):
        assert drift_observation_state.should_restart_after_observation(2, 2)

    def test_above_threshold_restarts(self):
        assert drift_observation_state.should_restart_after_observation(3, 2)


class TestDriftObservationCountStateRoundTrip:
    def test_write_then_read_returns_written_count(self, tmp_path):
        state_file_path = tmp_path / "state.json"
        drift_observation_state.write_consecutive_drift_observation_count(
            state_file_path, 1
        )
        assert (
            drift_observation_state.read_consecutive_drift_observation_count(
                state_file_path
            )
            == 1
        )

    def test_missing_file_reads_zero(self, tmp_path):
        assert (
            drift_observation_state.read_consecutive_drift_observation_count(
                tmp_path / "absent.json"
            )
            == 0
        )

    def test_corrupt_file_reads_zero(self, tmp_path):
        state_file_path = tmp_path / "corrupt.json"
        state_file_path.write_text("not json")
        assert (
            drift_observation_state.read_consecutive_drift_observation_count(
                state_file_path
            )
            == 0
        )
