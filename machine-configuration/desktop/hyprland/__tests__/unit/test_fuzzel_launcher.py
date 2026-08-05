from unittest.mock import patch

import fuzzel_launcher


class TestMergeFuzzelConfigs:
    def test_returns_none_when_theme_colors_missing(self, tmp_path):
        theme_colors = tmp_path / "theme" / "fuzzel.ini"
        base_config = tmp_path / "base" / "fuzzel.ini"
        merged_config = tmp_path / "cache" / "fuzzel-merged.ini"

        with (
            patch.object(fuzzel_launcher, "THEME_COLORS_PATH", theme_colors),
            patch.object(fuzzel_launcher, "BASE_CONFIG_PATH", base_config),
            patch.object(fuzzel_launcher, "MERGED_CONFIG_PATH", merged_config),
        ):
            result = fuzzel_launcher.merge_fuzzel_configs()
            assert result is None

    def test_merges_base_and_theme_configs(self, tmp_path):
        base_config = tmp_path / "base" / "fuzzel.ini"
        base_config.parent.mkdir(parents=True)
        base_config.write_text("[main]\nfont=monospace\n")

        theme_colors = tmp_path / "theme" / "fuzzel.ini"
        theme_colors.parent.mkdir(parents=True)
        theme_colors.write_text("[colors]\nbackground=000000ff\n")

        merged_config = tmp_path / "cache" / "fuzzel-merged.ini"

        with (
            patch.object(fuzzel_launcher, "THEME_COLORS_PATH", theme_colors),
            patch.object(fuzzel_launcher, "BASE_CONFIG_PATH", base_config),
            patch.object(fuzzel_launcher, "MERGED_CONFIG_PATH", merged_config),
        ):
            merged = fuzzel_launcher.merge_fuzzel_configs()
            assert merged is not None
            content = merged.read_text()
            assert "[main]" in content
            assert "font=monospace" in content
            assert "[colors]" in content
            assert "background=000000ff" in content

    def test_handles_missing_base_config(self, tmp_path):
        base_config = tmp_path / "base" / "fuzzel.ini"
        theme_colors = tmp_path / "theme" / "fuzzel.ini"
        theme_colors.parent.mkdir(parents=True)
        theme_colors.write_text("[colors]\nbackground=000000ff\n")

        merged_config = tmp_path / "cache" / "fuzzel-merged.ini"

        with (
            patch.object(fuzzel_launcher, "THEME_COLORS_PATH", theme_colors),
            patch.object(fuzzel_launcher, "BASE_CONFIG_PATH", base_config),
            patch.object(fuzzel_launcher, "MERGED_CONFIG_PATH", merged_config),
        ):
            merged = fuzzel_launcher.merge_fuzzel_configs()
            assert merged is not None
            content = merged.read_text()
            assert "[colors]" in content

    def test_creates_cache_directory(self, tmp_path):
        theme_colors = tmp_path / "theme" / "fuzzel.ini"
        theme_colors.parent.mkdir(parents=True)
        theme_colors.write_text("[colors]\n")

        merged_config = tmp_path / "cache" / "nested" / "fuzzel-merged.ini"

        with (
            patch.object(fuzzel_launcher, "THEME_COLORS_PATH", theme_colors),
            patch.object(fuzzel_launcher, "BASE_CONFIG_PATH", tmp_path / "noexist.ini"),
            patch.object(fuzzel_launcher, "MERGED_CONFIG_PATH", merged_config),
        ):
            merged = fuzzel_launcher.merge_fuzzel_configs()
            assert merged is not None
            assert merged.parent.exists()


class TestMain:
    def test_launches_fuzzel_with_merged_config(self, tmp_path):
        merged_path = tmp_path / "merged.ini"

        with patch("fuzzel_launcher.merge_fuzzel_configs", return_value=merged_path):
            with patch("fuzzel_launcher.sys.argv", ["cmd"]):
                with patch("fuzzel_launcher.os.execvp") as mock_exec:
                    fuzzel_launcher.main()
                    mock_exec.assert_called_once_with(
                        "fuzzel",
                        ["fuzzel", f"--config={merged_path}"],
                    )

    def test_launches_fuzzel_without_config_when_no_theme(self):
        with patch("fuzzel_launcher.merge_fuzzel_configs", return_value=None):
            with patch("fuzzel_launcher.sys.argv", ["cmd"]):
                with patch("fuzzel_launcher.os.execvp") as mock_exec:
                    fuzzel_launcher.main()
                    mock_exec.assert_called_once_with("fuzzel", ["fuzzel"])

    def test_passes_extra_args_to_fuzzel(self, tmp_path):
        merged_path = tmp_path / "merged.ini"

        with patch("fuzzel_launcher.merge_fuzzel_configs", return_value=merged_path):
            with patch(
                "fuzzel_launcher.sys.argv",
                ["cmd", "--dmenu", "--prompt=Select:"],
            ):
                with patch("fuzzel_launcher.os.execvp") as mock_exec:
                    fuzzel_launcher.main()
                    mock_exec.assert_called_once_with(
                        "fuzzel",
                        [
                            "fuzzel",
                            f"--config={merged_path}",
                            "--dmenu",
                            "--prompt=Select:",
                        ],
                    )
