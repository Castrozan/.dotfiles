from repair_wallpaper_links import repair_wallpaper_links


def test_repairs_current_and_cached_theme_without_changing_selection(tmp_path):
    theme = tmp_path / "theme"
    legacy = tmp_path / "old-repo/wallpapers"
    image = tmp_path / "new-repo/gruvbox.jpg"
    image.parent.mkdir()
    image.write_bytes(b"image")
    catalog = tmp_path / "wallpapers"
    catalog.mkdir()
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
    assert repair_wallpaper_links(theme, catalog, (legacy,)) == 2
    assert current.readlink() == links[0]
    assert current.resolve() == image
    assert all(link.resolve() == image for link in links)
    assert repair_wallpaper_links(theme, catalog, (legacy,)) == 0


def test_repairs_direct_current_background(tmp_path):
    theme = tmp_path / "theme"
    legacy = tmp_path / "old-repo/wallpapers"
    catalog = tmp_path / "wallpapers"
    (theme / "current").mkdir(parents=True)
    catalog.mkdir()
    image = catalog / "gruvbox.jpg"
    image.write_bytes(b"image")
    current = theme / "current/background"
    current.symlink_to(legacy / "gruvbox.jpg")
    assert repair_wallpaper_links(theme, catalog, (legacy,)) == 1
    assert current.resolve() == image
