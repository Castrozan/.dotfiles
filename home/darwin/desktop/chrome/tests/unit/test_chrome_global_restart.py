import chrome_global_restart

MAIN_COMMAND_LINE = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "--user-data-dir=/Users/someone/.config/chrome-global",
]
RENDERER_COMMAND_LINE = MAIN_COMMAND_LINE + ["--type=renderer"]


def _sequence_of_process_lists(*process_lists):
    remaining = list(process_lists)

    def find():
        return remaining.pop(0) if remaining else []

    return find


class TestTerminateChromeGlobalMainProcessesGracefully:
    def test_terminates_main_spares_children_and_reports_clean(
        self, fake_chrome_process, monkeypatch
    ):
        main_process = fake_chrome_process(command_line=MAIN_COMMAND_LINE)
        child_process = fake_chrome_process(command_line=RENDERER_COMMAND_LINE)
        monkeypatch.setattr(
            chrome_global_restart,
            "find_chrome_global_processes",
            _sequence_of_process_lists([main_process, child_process], []),
        )
        assert (
            chrome_global_restart.terminate_chrome_global_main_processes_gracefully(0.0)
            is True
        )
        assert main_process.terminate_called is True
        assert child_process.terminate_called is False

    def test_reports_dirty_when_processes_persist(
        self, fake_chrome_process, monkeypatch
    ):
        stuck_process = fake_chrome_process(command_line=RENDERER_COMMAND_LINE)
        monkeypatch.setattr(
            chrome_global_restart,
            "find_chrome_global_processes",
            lambda: [stuck_process],
        )
        assert (
            chrome_global_restart.terminate_chrome_global_main_processes_gracefully(0.0)
            is False
        )


class TestForceKillRemainingChromeGlobalProcesses:
    def test_kills_every_remaining_process(self, fake_chrome_process, monkeypatch):
        first = fake_chrome_process()
        second = fake_chrome_process()
        monkeypatch.setattr(
            chrome_global_restart,
            "find_chrome_global_processes",
            lambda: [first, second],
        )
        chrome_global_restart.force_kill_remaining_chrome_global_processes()
        assert first.kill_called is True
        assert second.kill_called is True


class TestRestartChromeGlobalRelaunchGuard:
    def test_relaunches_and_returns_true_when_teardown_clears(self, monkeypatch):
        relaunch_calls = []
        monkeypatch.setattr(
            chrome_global_restart,
            "terminate_chrome_global_main_processes_gracefully",
            lambda timeout_seconds: True,
        )
        monkeypatch.setattr(
            chrome_global_restart, "find_chrome_global_processes", lambda: []
        )
        monkeypatch.setattr(
            chrome_global_restart,
            "relaunch_chrome_global_via_launcher",
            lambda launcher_binary_path: relaunch_calls.append(launcher_binary_path),
        )
        result = chrome_global_restart.restart_chrome_global(
            "/launcher", "149.0.7827.197", {"149.0.7827.156"}
        )
        assert result is True
        assert relaunch_calls == ["/launcher"]

    def test_skips_relaunch_and_returns_false_when_processes_survive(
        self, fake_chrome_process, monkeypatch
    ):
        relaunch_calls = []
        monkeypatch.setattr(
            chrome_global_restart,
            "terminate_chrome_global_main_processes_gracefully",
            lambda timeout_seconds: False,
        )
        monkeypatch.setattr(
            chrome_global_restart,
            "force_kill_remaining_chrome_global_processes",
            lambda: None,
        )
        monkeypatch.setattr(
            chrome_global_restart,
            "find_chrome_global_processes",
            lambda: [fake_chrome_process()],
        )
        monkeypatch.setattr(
            chrome_global_restart,
            "relaunch_chrome_global_via_launcher",
            lambda launcher_binary_path: relaunch_calls.append(launcher_binary_path),
        )
        monkeypatch.setattr(chrome_global_restart.time, "sleep", lambda seconds: None)
        result = chrome_global_restart.restart_chrome_global(
            "/launcher", "149.0.7827.197", {"149.0.7827.156"}
        )
        assert result is False
        assert relaunch_calls == []
