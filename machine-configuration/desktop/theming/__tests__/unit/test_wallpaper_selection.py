import regenerate_wallpaper_derived_colors as orchestrator


def test_find_returns_only_themes_carrying_the_marker(tmp_path, create_theme_directory):
    themes_directory = tmp_path / "static" / "themes"
    create_theme_directory(
        themes_directory,
        "derived",
        is_wallpaper_derived=True,
        background_filenames=["0-a.png"],
    )
    create_theme_directory(
        themes_directory,
        "curated",
        is_wallpaper_derived=False,
        background_filenames=["0-a.png"],
    )

    discovered = orchestrator.find_wallpaper_derived_theme_directories(themes_directory)

    assert [directory.name for directory in discovered] == ["derived"]


def test_find_is_empty_when_themes_directory_absent(tmp_path):
    assert (
        orchestrator.find_wallpaper_derived_theme_directories(tmp_path / "missing")
        == []
    )


def test_select_active_wallpaper_ignores_non_image_entries(tmp_path):
    backgrounds_directory = tmp_path / "backgrounds"
    backgrounds_directory.mkdir()
    (backgrounds_directory / ".DS_Store").write_bytes(b"\x00")
    (backgrounds_directory / "0-wave.png").write_bytes(b"image-bytes")

    selected = orchestrator.select_active_wallpaper_path(backgrounds_directory)

    assert selected is not None
    assert selected.name == "0-wave.png"


def test_select_active_wallpaper_picks_byte_first_image(tmp_path):
    backgrounds_directory = tmp_path / "backgrounds"
    backgrounds_directory.mkdir()
    for filename in ["great-wave.jpg", "0-tech.png", "aurora.webp"]:
        (backgrounds_directory / filename).write_bytes(b"image-bytes")

    selected = orchestrator.select_active_wallpaper_path(backgrounds_directory)

    assert selected is not None
    assert selected.name == "0-tech.png"


def test_select_active_wallpaper_is_none_without_images(tmp_path):
    backgrounds_directory = tmp_path / "backgrounds"
    backgrounds_directory.mkdir()
    (backgrounds_directory / ".DS_Store").write_bytes(b"\x00")

    assert orchestrator.select_active_wallpaper_path(backgrounds_directory) is None
