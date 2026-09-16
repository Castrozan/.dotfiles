import subprocess
from pathlib import Path

THEME_PATH = Path.home() / ".config" / "hypr-theme" / "current" / "theme"


def set_gnome_color_scheme_from_theme() -> None:
    if (THEME_PATH / "light.mode").is_file():
        scheme = "prefer-light"
    else:
        scheme = "prefer-dark"
    subprocess.run(
        ["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", scheme]
    )


def set_gnome_icon_theme_from_theme() -> None:
    icons_file = THEME_PATH / "icons.theme"
    if not icons_file.is_file():
        return
    icon_theme = icons_file.read_text().strip()
    subprocess.run(
        ["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", icon_theme]
    )


def main() -> None:
    set_gnome_color_scheme_from_theme()
    set_gnome_icon_theme_from_theme()


if __name__ == "__main__":
    main()
