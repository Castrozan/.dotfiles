import re
import subprocess
import tomllib
from pathlib import Path

CURRENT_THEME_PATH = Path.home() / ".config" / "hypr-theme" / "current" / "theme"
HERDR_CONFIG = Path.home() / ".config" / "herdr" / "config.toml"


def read_accent_from_current_theme_colors() -> str | None:
    colors_file = CURRENT_THEME_PATH / "colors.toml"
    if not colors_file.is_file():
        return None
    with colors_file.open("rb") as colors_file_handle:
        colors = tomllib.load(colors_file_handle)
    return colors.get("accent")


def rewrite_herdr_accent_line(config_text: str, accent: str) -> str:
    return re.sub(
        r"^accent = .*$",
        f'accent = "{accent}"',
        config_text,
        flags=re.MULTILINE,
    )


def reload_running_herdr_server() -> None:
    subprocess.run(["herdr", "server", "reload-config"], capture_output=True)


def update_herdr_accent_in_config() -> None:
    if not HERDR_CONFIG.is_file():
        return
    accent = read_accent_from_current_theme_colors()
    if accent is None:
        return
    config_text = HERDR_CONFIG.read_text()
    updated_config_text = rewrite_herdr_accent_line(config_text, accent)
    if updated_config_text == config_text:
        return
    HERDR_CONFIG.write_text(updated_config_text)
    reload_running_herdr_server()


def main() -> None:
    update_herdr_accent_in_config()


if __name__ == "__main__":
    main()
