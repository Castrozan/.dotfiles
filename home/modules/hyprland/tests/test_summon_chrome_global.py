import summon_chrome_global as summoner


class TestFindChromeGlobalWindowByHyprlandTag:
    def test_finds_tagged_window(self, hyprctl_response_builder):
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
        result = summoner.find_chrome_global_window_by_hyprland_tag()
        assert result["address"] == "0xa"

    def test_returns_none_when_no_tag(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "clients",
            [
                {
                    "class": "chrome-global",
                    "address": "0xa",
                    "tags": [],
                    "workspace": {"id": 1},
                }
            ],
        )
        result = summoner.find_chrome_global_window_by_hyprland_tag()
        assert result is None

    def test_returns_none_when_no_chrome_global(self, hyprctl_response_builder):
        hyprctl_response_builder("clients", [])
        result = summoner.find_chrome_global_window_by_hyprland_tag()
        assert result is None


class TestFindChromeGlobalWindowByTitlePattern:
    def test_finds_window_with_chat_title(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "clients",
            [
                {
                    "class": "chrome-global",
                    "address": "0xa",
                    "title": "Google Chat - Inbox",
                    "floating": False,
                    "workspace": {"id": 1},
                }
            ],
        )
        result = summoner.find_chrome_global_window_by_title_pattern()
        assert result["address"] == "0xa"

    def test_finds_window_with_agenda_title(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "clients",
            [
                {
                    "class": "chrome-global",
                    "address": "0xa",
                    "title": "My Agenda",
                    "floating": False,
                    "workspace": {"id": 1},
                }
            ],
        )
        result = summoner.find_chrome_global_window_by_title_pattern()
        assert result["address"] == "0xa"

    def test_skips_floating_windows(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "clients",
            [
                {
                    "class": "chrome-global",
                    "address": "0xa",
                    "title": "Google Chat",
                    "floating": True,
                    "workspace": {"id": 1},
                }
            ],
        )
        result = summoner.find_chrome_global_window_by_title_pattern()
        assert result is None

    def test_returns_none_when_title_does_not_match(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "clients",
            [
                {
                    "class": "chrome-global",
                    "address": "0xa",
                    "title": "Settings",
                    "floating": False,
                    "workspace": {"id": 1},
                }
            ],
        )
        result = summoner.find_chrome_global_window_by_title_pattern()
        assert result is None


class TestFindChromeGlobalWindowByInitialTitlePattern:
    def test_finds_window_by_initial_title(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "clients",
            [
                {
                    "class": "chrome-global",
                    "address": "0xa",
                    "title": "Settings",
                    "initialTitle": "Google Chat",
                    "floating": False,
                    "workspace": {"id": 1},
                }
            ],
        )
        result = summoner.find_chrome_global_window_by_initial_title_pattern()
        assert result["address"] == "0xa"


class TestFindChromeGlobalMainWindow:
    def test_prefers_tagged_window(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "clients",
            [
                {
                    "class": "chrome-global",
                    "address": "0xa",
                    "tags": ["chrome-global-main-window"],
                    "title": "Settings",
                    "floating": False,
                    "workspace": {"id": 1},
                },
                {
                    "class": "chrome-global",
                    "address": "0xb",
                    "tags": [],
                    "title": "Google Chat",
                    "floating": False,
                    "workspace": {"id": 1},
                },
            ],
        )
        result = summoner.find_chrome_global_main_window()
        assert result["address"] == "0xa"

    def test_falls_back_to_title_pattern_and_tags(
        self, mock_subprocess_run, hyprctl_response_builder
    ):
        hyprctl_response_builder(
            "clients",
            [
                {
                    "class": "chrome-global",
                    "address": "0xb",
                    "tags": [],
                    "title": "Google Chat",
                    "floating": False,
                    "workspace": {"id": 1},
                }
            ],
        )
        result = summoner.find_chrome_global_main_window()
        assert result["address"] == "0xb"
        tag_calls = [
            c for c in mock_subprocess_run.call_args_list if "tagwindow" in str(c)
        ]
        assert len(tag_calls) > 0

    def test_returns_none_when_no_chrome_global(self, hyprctl_response_builder):
        hyprctl_response_builder("clients", [])
        result = summoner.find_chrome_global_main_window()
        assert result is None


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
            if "hypr-detach-from-group-and-move-to-workspace" in str(c)
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
