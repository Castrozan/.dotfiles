import summon_chrome_global as summoner


class TestSummonOrLaunchChromeGlobal:
    def test_focuses_window_on_same_workspace(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder("activeworkspace", {"id": 1})
        hyprctl_response_builder(
            "clients",
            [
                {
                    "class": "chrome-global",
                    "address": "0xa",
                    "tags": ["chrome-global-main-window"],
                    "workspace": {"id": 1},
                }
            ],
        )
        summoner.summon_or_launch_chrome_global()
        dispatch_calls = [
            c for c in mock_subprocess_run.call_args_list if "focuswindow" in str(c)
        ]
        assert len(dispatch_calls) > 0

    def test_detaches_and_moves_from_different_workspace(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder("activeworkspace", {"id": 1})
        hyprctl_response_builder(
            "clients",
            [
                {
                    "class": "chrome-global",
                    "address": "0xa",
                    "tags": ["chrome-global-main-window"],
                    "workspace": {"id": 2},
                }
            ],
        )
        summoner.summon_or_launch_chrome_global()
        detach_calls = [
            c
            for c in mock_subprocess_run.call_args_list
            if "hypr-move-window-to-workspace" in str(c)
        ]
        assert len(detach_calls) == 1


class TestInitializeChromeGlobalProfileIfNeeded:
    def test_creates_profile_directory_and_preferences(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            summoner, "CHROME_GLOBAL_DATA_DIR", tmp_path / "chrome-global"
        )
        summoner.initialize_chrome_global_profile_if_needed()
        prefs = tmp_path / "chrome-global" / "Default" / "Preferences"
        assert prefs.exists()
        assert "restore_on_startup" in prefs.read_text()

    def test_skips_when_profile_already_exists(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "chrome-global"
        (data_dir / "Default").mkdir(parents=True)
        monkeypatch.setattr(summoner, "CHROME_GLOBAL_DATA_DIR", data_dir)
        summoner.initialize_chrome_global_profile_if_needed()
        assert not (data_dir / "Default" / "Preferences").exists()


class TestChromeGlobalHasNeverBeenLaunched:
    def test_returns_true_when_no_marker(self, tmp_path, monkeypatch):
        monkeypatch.setattr(summoner, "CHROME_GLOBAL_DATA_DIR", tmp_path)
        assert summoner.chrome_global_has_never_been_launched()

    def test_returns_false_when_marker_exists(self, tmp_path, monkeypatch):
        (tmp_path / ".initialized").touch()
        monkeypatch.setattr(summoner, "CHROME_GLOBAL_DATA_DIR", tmp_path)
        assert not summoner.chrome_global_has_never_been_launched()
