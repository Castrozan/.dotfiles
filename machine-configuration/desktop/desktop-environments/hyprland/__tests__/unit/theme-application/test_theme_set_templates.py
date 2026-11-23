import theme_set_templates as tst


class TestProcessAllTemplates:
    def test_processes_strip_and_rgb_variants(self, tmp_path, monkeypatch):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "test.css.tpl").write_text(
            "hex: {{ accent }}; raw: {{ accent_strip }}; rgb: {{ accent_rgb }}"
        )

        next_theme_dir = tmp_path / "next-theme"
        next_theme_dir.mkdir()
        colors_file = next_theme_dir / "colors.toml"
        colors_file.write_text('accent = "#89b4fa"\n')

        monkeypatch.setattr(tst, "TEMPLATES_DIR", templates_dir)
        monkeypatch.setattr(tst, "USER_TEMPLATES_DIR", tmp_path / "user-templates")
        monkeypatch.setattr(tst, "NEXT_THEME_DIR", next_theme_dir)
        monkeypatch.setattr(tst, "COLORS_FILE", colors_file)

        tst.process_all_templates()

        output = next_theme_dir / "test.css"
        assert output.read_text() == "hex: #89b4fa; raw: 89b4fa; rgb: 137,180,250"
