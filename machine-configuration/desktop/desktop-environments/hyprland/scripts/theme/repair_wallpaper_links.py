"""Repair saved theme links after the repository wallpaper layout moves."""

from pathlib import Path


def repair_wallpaper_links(theme_root: Path, wallpaper_roots: tuple[Path, ...]) -> int:
    catalog = theme_root / "wallpapers"
    links = list((theme_root / "current/theme/backgrounds").glob("*"))
    links.extend((theme_root / "user-themes").glob("*/backgrounds/*"))
    links.append(theme_root / "current/background")
    repaired = 0
    for link in links:
        if not link.is_symlink() or link.exists():
            continue
        old_target = link.resolve()
        if not any(old_target.is_relative_to(root) for root in wallpaper_roots):
            continue
        replacement = catalog / old_target.name
        if not replacement.is_file():
            continue
        link.unlink()
        link.symlink_to(replacement)
        repaired += 1
    return repaired


def main() -> None:
    home = Path.home()
    desktop = home / ".dotfiles/machine-configuration/desktop"
    repaired = repair_wallpaper_links(
        home / ".config/hypr-theme",
        (desktop / "theming/wallpapers", desktop / "appearance/theming/wallpapers"),
    )
    print(f"Repaired {repaired} moved wallpaper references")


if __name__ == "__main__":
    main()
