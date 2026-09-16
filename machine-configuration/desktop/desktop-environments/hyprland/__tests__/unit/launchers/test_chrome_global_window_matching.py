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
