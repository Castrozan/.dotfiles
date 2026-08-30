import ambient_canvas_theme as theme


def test_resolve_theme_background_reads_the_active_theme(tmp_path):
    colors_path = tmp_path / "colors.toml"
    colors_path.write_text('background = "#241010"\n')

    assert theme.resolve_theme_background_color(str(colors_path)) == "#241010"


def test_resolve_theme_background_normalizes_hexadecimal_case(tmp_path):
    colors_path = tmp_path / "colors.toml"
    colors_path.write_text('background = "#A1B2C3"\n')

    assert theme.resolve_theme_background_color(str(colors_path)) == "#a1b2c3"


def test_resolve_theme_background_falls_back_when_the_file_is_absent(tmp_path):
    assert theme.resolve_theme_background_color(str(tmp_path / "absent.toml")) == (
        theme.DEFAULT_BACKGROUND_COLOR_HEX
    )


def test_resolve_theme_background_falls_back_when_the_value_is_invalid(tmp_path):
    colors_path = tmp_path / "colors.toml"
    colors_path.write_text('background = "navy"\n')

    assert theme.resolve_theme_background_color(str(colors_path)) == (
        theme.DEFAULT_BACKGROUND_COLOR_HEX
    )


def test_resolve_theme_background_falls_back_when_the_toml_is_malformed(tmp_path):
    colors_path = tmp_path / "colors.toml"
    colors_path.write_text('background = "')

    assert theme.resolve_theme_background_color(str(colors_path)) == (
        theme.DEFAULT_BACKGROUND_COLOR_HEX
    )


def test_theme_background_participates_in_the_recording_identity():
    assert theme.compose_theme_source_identifier("/store/web", "#241010") == (
        "/store/web theme-background=#241010"
    )
