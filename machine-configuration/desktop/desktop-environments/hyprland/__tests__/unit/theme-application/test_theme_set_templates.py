import theme_set_templates as tst


class TestHexColorToRgbString:
    def test_converts_pure_red(self):
        assert tst.hex_color_to_rgb_string("#ff0000") == "255,0,0"

    def test_converts_pure_green(self):
        assert tst.hex_color_to_rgb_string("#00ff00") == "0,255,0"

    def test_converts_pure_blue(self):
        assert tst.hex_color_to_rgb_string("#0000ff") == "0,0,255"

    def test_converts_mixed_color(self):
        assert tst.hex_color_to_rgb_string("#1a2b3c") == "26,43,60"

    def test_handles_without_hash_prefix(self):
        assert tst.hex_color_to_rgb_string("ff0000") == "255,0,0"


class TestLoadColorSubstitutions:
    def test_loads_hex_color_with_all_variants(self, tmp_path):
        colors_file = tmp_path / "colors.toml"
        colors_file.write_text('primary = "#ff0000"\n')
        result = tst.load_color_substitutions(colors_file)
        assert result["{{ primary }}"] == "#ff0000"
        assert result["{{ primary_strip }}"] == "ff0000"
        assert result["{{ primary_rgb }}"] == "255,0,0"

    def test_loads_non_hex_value_without_rgb_variant(self, tmp_path):
        colors_file = tmp_path / "colors.toml"
        colors_file.write_text("font_size = 14\n")
        result = tst.load_color_substitutions(colors_file)
        assert result["{{ font_size }}"] == "14"
        assert "{{ font_size_rgb }}" not in result

    def test_loads_multiple_colors(self, tmp_path):
        colors_file = tmp_path / "colors.toml"
        colors_file.write_text('accent = "#89b4fa"\nbackground = "#1e1e2e"\n')
        result = tst.load_color_substitutions(colors_file)
        assert result["{{ accent }}"] == "#89b4fa"
        assert result["{{ background }}"] == "#1e1e2e"
        assert result["{{ accent_strip }}"] == "89b4fa"
        assert result["{{ background_strip }}"] == "1e1e2e"


class TestApplySubstitutionsToTemplate:
    def test_replaces_all_placeholders(self):
        template = "color: {{ primary }}; bg: {{ secondary }}"
        substitutions = {"{{ primary }}": "#ff0000", "{{ secondary }}": "#00ff00"}
        result = tst.apply_substitutions_to_template(template, substitutions)
        assert result == "color: #ff0000; bg: #00ff00"

    def test_leaves_unknown_placeholders_intact(self):
        template = "color: {{ unknown }}"
        result = tst.apply_substitutions_to_template(template, {})
        assert result == "color: {{ unknown }}"

    def test_replaces_multiple_occurrences(self):
        template = "{{ c }} and {{ c }}"
        result = tst.apply_substitutions_to_template(template, {"{{ c }}": "red"})
        assert result == "red and red"


class TestFindAllTemplateFiles:
    def test_finds_templates_recursively(self, tmp_path, monkeypatch):
        templates_dir = tmp_path / "templates"
        sub_dir = templates_dir / "apps"
        sub_dir.mkdir(parents=True)
        (sub_dir / "test.conf.tpl").touch()
        (templates_dir / "root.ini.tpl").touch()

        monkeypatch.setattr(tst, "TEMPLATES_DIR", templates_dir)
        monkeypatch.setattr(tst, "USER_TEMPLATES_DIR", tmp_path / "nonexistent")

        result = tst.find_all_template_files()
        assert len(result) == 2

    def test_returns_empty_when_no_directories(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tst, "TEMPLATES_DIR", tmp_path / "a")
        monkeypatch.setattr(tst, "USER_TEMPLATES_DIR", tmp_path / "b")
        result = tst.find_all_template_files()
        assert result == []


class TestProcessAllTemplates:
    def test_processes_templates_with_color_substitutions(self, tmp_path, monkeypatch):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "test.conf.tpl").write_text("color = {{ primary }}")

        next_theme_dir = tmp_path / "next-theme"
        next_theme_dir.mkdir()
        colors_file = next_theme_dir / "colors.toml"
        colors_file.write_text('primary = "#ff0000"\n')

        monkeypatch.setattr(tst, "TEMPLATES_DIR", templates_dir)
        monkeypatch.setattr(tst, "USER_TEMPLATES_DIR", tmp_path / "user-templates")
        monkeypatch.setattr(tst, "NEXT_THEME_DIR", next_theme_dir)
        monkeypatch.setattr(tst, "COLORS_FILE", colors_file)

        tst.process_all_templates()

        output = next_theme_dir / "test.conf"
        assert output.exists()
        assert output.read_text() == "color = #ff0000"

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

    def test_skips_when_no_colors_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tst, "COLORS_FILE", tmp_path / "nonexistent.toml")
        tst.process_all_templates()

    def test_handles_templates_in_subdirectories(self, tmp_path, monkeypatch):
        templates_dir = tmp_path / "templates"
        sub_dir = templates_dir / "apps"
        sub_dir.mkdir(parents=True)
        (sub_dir / "app.ini.tpl").write_text("bg = {{ background }}")

        next_theme_dir = tmp_path / "next-theme"
        next_theme_dir.mkdir()
        colors_file = next_theme_dir / "colors.toml"
        colors_file.write_text('background = "#1e1e2e"\n')

        monkeypatch.setattr(tst, "TEMPLATES_DIR", templates_dir)
        monkeypatch.setattr(tst, "USER_TEMPLATES_DIR", tmp_path / "user-templates")
        monkeypatch.setattr(tst, "NEXT_THEME_DIR", next_theme_dir)
        monkeypatch.setattr(tst, "COLORS_FILE", colors_file)

        tst.process_all_templates()

        output = next_theme_dir / "app.ini"
        assert output.exists()
        assert output.read_text() == "bg = #1e1e2e"
