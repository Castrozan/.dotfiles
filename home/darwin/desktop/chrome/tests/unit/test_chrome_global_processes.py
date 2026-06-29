import chrome_global_processes
import chrome_version_detection
import psutil

CHROME_GLOBAL_USER_DATA_DIRECTORY = (
    chrome_global_processes.CHROME_GLOBAL_USER_DATA_DIRECTORY
)

MAIN_COMMAND_LINE = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    f"--user-data-dir={CHROME_GLOBAL_USER_DATA_DIRECTORY}",
]
RENDERER_COMMAND_LINE = MAIN_COMMAND_LINE + ["--type=renderer"]
OTHER_PROFILE_COMMAND_LINE = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "--user-data-dir=/Users/someone/Library/Application Support/Google/Chrome",
]
MAIN_EXECUTABLE_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HELPER_EXECUTABLE_PATH = (
    "/Applications/Google Chrome.app/Contents/Frameworks/"
    "Google Chrome Framework.framework/Versions/149.0.7827.156/"
    "Helpers/Google Chrome Helper.app/Contents/MacOS/Google Chrome Helper"
)


class TestProcessBelongsToChromeGlobal:
    def test_true_for_chrome_global_user_data_dir(self, fake_chrome_process):
        assert chrome_global_processes.process_belongs_to_chrome_global(
            fake_chrome_process(command_line=MAIN_COMMAND_LINE)
        )

    def test_false_for_other_profile(self, fake_chrome_process):
        assert not chrome_global_processes.process_belongs_to_chrome_global(
            fake_chrome_process(command_line=OTHER_PROFILE_COMMAND_LINE)
        )


class TestProcessIsChromeChild:
    def test_true_when_type_flag_present(self, fake_chrome_process):
        assert chrome_global_processes.process_is_chrome_child(
            fake_chrome_process(command_line=RENDERER_COMMAND_LINE)
        )

    def test_false_for_main_process(self, fake_chrome_process):
        assert not chrome_global_processes.process_is_chrome_child(
            fake_chrome_process(command_line=MAIN_COMMAND_LINE)
        )


class TestJoinedCommandLineForProcess:
    def test_returns_empty_on_access_error(self, fake_chrome_process):
        process = fake_chrome_process(access_error=psutil.AccessDenied())
        assert chrome_global_processes.joined_command_line_for_process(process) == ""


class TestCollectRunningFrameworkVersions:
    def test_collects_helper_version_skipping_main_and_access_errors(
        self, fake_chrome_process
    ):
        processes = [
            fake_chrome_process(executable_path=MAIN_EXECUTABLE_PATH),
            fake_chrome_process(executable_path=HELPER_EXECUTABLE_PATH),
            fake_chrome_process(access_error=psutil.NoSuchProcess(1)),
        ]
        assert chrome_version_detection.collect_running_framework_versions(
            processes
        ) == {"149.0.7827.156"}
