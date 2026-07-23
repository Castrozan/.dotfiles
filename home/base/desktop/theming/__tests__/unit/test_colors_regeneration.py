import sys

import regenerate_wallpaper_derived_colors as orchestrator


def test_regenerate_writes_and_stages_wallpaper_and_colors_when_palette_differs(
    tmp_path, monkeypatch, create_theme_directory, record_staged_paths
):
    themes_directory = tmp_path / "static" / "themes"
    theme_directory = create_theme_directory(
        themes_directory,
        "derived",
        is_wallpaper_derived=True,
        background_filenames=["0-wave.png"],
        existing_colors_toml='accent = "#000000"\n',
    )
    monkeypatch.setattr(
        orchestrator,
        "generate_colors_toml_for_image_path",
        lambda wallpaper_image_path: 'accent = "#c17013"\n',
    )

    orchestrator.regenerate_theme_colors_if_wallpaper_palette_changed(
        tmp_path, theme_directory
    )

    assert (theme_directory / "colors.toml").read_text() == 'accent = "#c17013"\n'
    assert [path.name for path in record_staged_paths] == ["0-wave.png", "colors.toml"]


def test_regenerate_does_not_write_when_palette_is_identical(
    tmp_path, monkeypatch, create_theme_directory, record_staged_paths
):
    themes_directory = tmp_path / "static" / "themes"
    theme_directory = create_theme_directory(
        themes_directory,
        "derived",
        is_wallpaper_derived=True,
        background_filenames=["0-wave.png"],
        existing_colors_toml='accent = "#c17013"\n',
    )
    monkeypatch.setattr(
        orchestrator,
        "generate_colors_toml_for_image_path",
        lambda wallpaper_image_path: 'accent = "#c17013"\n',
    )

    orchestrator.regenerate_theme_colors_if_wallpaper_palette_changed(
        tmp_path, theme_directory
    )

    assert record_staged_paths == []


def test_regenerate_writes_when_colors_toml_missing(
    tmp_path, monkeypatch, create_theme_directory, record_staged_paths
):
    themes_directory = tmp_path / "static" / "themes"
    theme_directory = create_theme_directory(
        themes_directory,
        "derived",
        is_wallpaper_derived=True,
        background_filenames=["0-wave.png"],
    )
    monkeypatch.setattr(
        orchestrator,
        "generate_colors_toml_for_image_path",
        lambda wallpaper_image_path: 'accent = "#c17013"\n',
    )

    orchestrator.regenerate_theme_colors_if_wallpaper_palette_changed(
        tmp_path, theme_directory
    )

    assert (theme_directory / "colors.toml").is_file()
    assert [path.name for path in record_staged_paths] == ["0-wave.png", "colors.toml"]


def test_main_isolates_a_failing_theme_from_the_rest(
    tmp_path, monkeypatch, create_theme_directory, record_staged_paths
):
    themes_directory = tmp_path / "static" / "themes"
    create_theme_directory(
        themes_directory,
        "broken",
        is_wallpaper_derived=True,
        background_filenames=["0-broken.png"],
    )
    healthy_theme_directory = create_theme_directory(
        themes_directory,
        "healthy",
        is_wallpaper_derived=True,
        background_filenames=["0-healthy.png"],
    )

    def generate_but_fail_for_broken(wallpaper_image_path):
        if wallpaper_image_path.name == "0-broken.png":
            raise RuntimeError("corrupt image")
        return 'accent = "#c17013"\n'

    monkeypatch.setattr(
        orchestrator,
        "generate_colors_toml_for_image_path",
        generate_but_fail_for_broken,
    )
    monkeypatch.setattr(sys, "argv", ["theme-regenerate", str(tmp_path)])

    orchestrator.main()

    assert (healthy_theme_directory / "colors.toml").is_file()
    assert not (themes_directory / "broken" / "colors.toml").is_file()
