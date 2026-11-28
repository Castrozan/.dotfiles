from unittest.mock import Mock

import pytest

from playback.mpv_theme_screen_blend import (
    ThemeScreenBlend,
    build_screen_blend_shader,
)


@pytest.mark.parametrize(
    ("background_hex", "backdrop_literal"),
    [
        ("#000000", "vec3(0.000000, 0.000000, 0.000000)"),
        ("#ff8000", "vec3(1.000000, 0.501961, 0.000000)"),
    ],
)
def test_the_shader_screens_the_theme_background_over_the_recorded_frame(
    background_hex, backdrop_literal
):
    shader = build_screen_blend_shader(background_hex)
    assert "//!HOOK OUTPUT" in shader
    assert backdrop_literal in shader
    assert "vec3(1.0) - (vec3(1.0) - content) * (vec3(1.0) - backdrop)" in shader


def test_the_blend_loads_a_fresh_shader_only_when_the_theme_background_changes(
    tmp_path,
):
    colors_path = tmp_path / "colors.toml"
    mpv_client = Mock()
    blend = ThemeScreenBlend(mpv_client, str(colors_path), str(tmp_path))
    first_shader_path = tmp_path / "theme-112233.glsl"
    second_shader_path = tmp_path / "theme-445566.glsl"

    colors_path.write_text('background = "#112233"\n')
    blend.synchronize()
    blend.synchronize()
    assert "0.066667, 0.133333, 0.200000" in first_shader_path.read_text()
    mpv_client.send_command.assert_called_once_with(
        ["change-list", "glsl-shaders", "set", str(first_shader_path)]
    )

    colors_path.write_text('background = "#445566"\n')
    blend.synchronize()
    assert "0.266667, 0.333333, 0.400000" in second_shader_path.read_text()
    assert not first_shader_path.exists()
    mpv_client.send_command.assert_called_with(
        ["change-list", "glsl-shaders", "set", str(second_shader_path)]
    )
    assert mpv_client.send_command.call_count == 2
