from pathlib import Path

from repair_wallpaper_links import repair_wallpaper_links


def test_repairs_current_and_cached_theme_without_changing_selection(tmp_path):
    theme = tmp_path / "theme"
    legacy = tmp_path / "old-repo/wallpapers"
    image = tmp_path / "new-repo/gruvbox.jpg"
    image.parent.mkdir()
    image.write_bytes(b"image")
    catalog = theme / "wallpapers"
    catalog.mkdir(parents=True)
    (catalog / image.name).symlink_to(image)
    links = [
        theme / "current/theme/backgrounds/gruvbox.jpg",
        theme / "user-themes/auto-gruvbox/backgrounds/gruvbox.jpg",
    ]
    for link in links:
        link.parent.mkdir(parents=True)
        link.symlink_to(legacy / image.name)
    current = theme / "current/background"
    current.symlink_to(links[0])
    assert repair_wallpaper_links(theme, (legacy,)) == 2
    assert current.readlink() == links[0]
    assert current.resolve() == image
    assert all(link.resolve() == image for link in links)
    assert repair_wallpaper_links(theme, (legacy,)) == 0


def test_preserves_valid_external_and_unknown_wallpapers(tmp_path):
    theme = tmp_path / "theme"
    legacy = tmp_path / "old-repo/wallpapers"
    backgrounds = theme / "current/theme/backgrounds"
    backgrounds.mkdir(parents=True)
    catalog = theme / "wallpapers"
    catalog.mkdir()
    custom = tmp_path / "custom.jpg"
    custom.write_bytes(b"custom")
    (catalog / "custom.jpg").symlink_to(custom)
    targets = {
        "valid.jpg": custom,
        "external.jpg": tmp_path / "external/custom.jpg",
        "unknown.jpg": legacy / "unknown.jpg",
    }
    for name, target in targets.items():
        (backgrounds / name).symlink_to(target)
    assert repair_wallpaper_links(theme, (legacy,)) == 0
    assert all(
        (backgrounds / name).readlink() == target for name, target in targets.items()
    )


def test_repairs_direct_current_background(tmp_path):
    theme = tmp_path / "theme"
    legacy = tmp_path / "old-repo/wallpapers"
    (theme / "current").mkdir(parents=True)
    (theme / "wallpapers").mkdir()
    image = theme / "wallpapers/gruvbox.jpg"
    image.write_bytes(b"image")
    current = theme / "current/background"
    current.symlink_to(legacy / "gruvbox.jpg")
    assert repair_wallpaper_links(theme, (legacy,)) == 1
    assert current.resolve() == image
