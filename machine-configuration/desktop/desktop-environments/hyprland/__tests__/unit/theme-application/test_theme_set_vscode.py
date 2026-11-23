import json

import theme_set


class TestUpdateVscodeColorCustomizations:
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
