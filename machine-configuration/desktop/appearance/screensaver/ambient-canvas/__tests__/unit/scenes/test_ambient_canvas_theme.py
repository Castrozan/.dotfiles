import pytest

import ambient_canvas_theme as theme


@pytest.mark.parametrize(
    ("colors_file_content", "resolved_background"),
    [
        ('background = "#A1B2C3"\n', "#a1b2c3"),
        ('background = "navy"\n', theme.DEFAULT_BACKGROUND_COLOR_HEX),
        (None, theme.DEFAULT_BACKGROUND_COLOR_HEX),
    ],
)
def test_resolve_theme_background_normalizes_or_falls_back(
    tmp_path, colors_file_content, resolved_background
):
    colors_path = tmp_path / "colors.toml"
    if colors_file_content is not None:
        colors_path.write_text(colors_file_content)

    assert theme.resolve_theme_background_color(str(colors_path)) == resolved_background


def test_recordings_are_theme_neutral_so_a_theme_switch_never_re_records():
    assert theme.RECORDING_BACKGROUND_COLOR_HEX == "#000000"
    assert not hasattr(theme, "compose_theme_source_identifier")
