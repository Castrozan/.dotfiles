import json

import theme_set


class TestUpdateVscodeColorCustomizations:
    def test_merges_color_overrides_into_existing_settings(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        (theme_path / "vscode-colors.json").write_text(
            json.dumps({"editor.background": "#1e1e2e", "editor.foreground": "#cdd6f4"})
        )

        vscode_settings = tmp_path / "settings.json"
        vscode_settings.write_text(
            json.dumps({"editor.fontSize": 14, "workbench.colorCustomizations": {}})
        )

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)
        monkeypatch.setattr(theme_set, "VSCODE_USER_SETTINGS", vscode_settings)

        theme_set.update_vscode_color_customizations()

        result = json.loads(vscode_settings.read_text())
        assert result["editor.fontSize"] == 14
        assert result["workbench.colorCustomizations"]["editor.background"] == "#1e1e2e"
        assert result["workbench.colorCustomizations"]["editor.foreground"] == "#cdd6f4"

    def test_replaces_previous_color_customizations(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        (theme_path / "vscode-colors.json").write_text(
            json.dumps({"editor.background": "#000000"})
        )

        vscode_settings = tmp_path / "settings.json"
        vscode_settings.write_text(
            json.dumps(
                {
                    "workbench.colorCustomizations": {
                        "editor.background": "#ffffff",
                        "sideBar.background": "#old",
                    }
                }
            )
        )

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)
        monkeypatch.setattr(theme_set, "VSCODE_USER_SETTINGS", vscode_settings)

        theme_set.update_vscode_color_customizations()

        result = json.loads(vscode_settings.read_text())
        assert result["workbench.colorCustomizations"] == {
            "editor.background": "#000000"
        }

    def test_does_nothing_when_no_generated_colors(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()

        vscode_settings = tmp_path / "settings.json"
        original_content = json.dumps({"editor.fontSize": 14})
        vscode_settings.write_text(original_content)

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)
        monkeypatch.setattr(theme_set, "VSCODE_USER_SETTINGS", vscode_settings)

        theme_set.update_vscode_color_customizations()

        assert vscode_settings.read_text() == original_content

    def test_does_nothing_when_no_vscode_settings(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        (theme_path / "vscode-colors.json").write_text(json.dumps({"a": "b"}))

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)
        monkeypatch.setattr(theme_set, "VSCODE_USER_SETTINGS", tmp_path / "nonexistent")

        theme_set.update_vscode_color_customizations()

    def test_preserves_other_settings_untouched(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        (theme_path / "vscode-colors.json").write_text(
            json.dumps({"editor.background": "#1e1e2e"})
        )

        vscode_settings = tmp_path / "settings.json"
        vscode_settings.write_text(
            json.dumps(
                {
                    "editor.fontSize": 14,
                    "window.zoomLevel": 1,
                    "workbench.preferredDarkColorTheme": "GitHub Dark Default",
                    "nix.serverPath": "nixd",
                }
            )
        )

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)
        monkeypatch.setattr(theme_set, "VSCODE_USER_SETTINGS", vscode_settings)

        theme_set.update_vscode_color_customizations()

        result = json.loads(vscode_settings.read_text())
        assert result["editor.fontSize"] == 14
        assert result["window.zoomLevel"] == 1
        assert result["workbench.preferredDarkColorTheme"] == "GitHub Dark Default"
        assert result["nix.serverPath"] == "nixd"
        assert "editor.background" in result["workbench.colorCustomizations"]

    def test_adds_color_customizations_key_when_absent(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        (theme_path / "vscode-colors.json").write_text(
            json.dumps({"statusBar.background": "#1e1e2e"})
        )

        vscode_settings = tmp_path / "settings.json"
        vscode_settings.write_text(json.dumps({"editor.fontSize": 14}))

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)
        monkeypatch.setattr(theme_set, "VSCODE_USER_SETTINGS", vscode_settings)

        theme_set.update_vscode_color_customizations()

        result = json.loads(vscode_settings.read_text())
        assert (
            result["workbench.colorCustomizations"]["statusBar.background"] == "#1e1e2e"
        )
