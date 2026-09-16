import re
import tomllib

DEFAULT_BACKGROUND_COLOR_HEX = "#0a1a2f"
HEX_COLOR_PATTERN = re.compile(r"#[0-9a-fA-F]{6}\Z")


def resolve_theme_background_color(theme_colors_path):
    if not theme_colors_path:
        return DEFAULT_BACKGROUND_COLOR_HEX
    try:
        with open(theme_colors_path, "rb") as theme_colors_file:
            theme_colors = tomllib.load(theme_colors_file)
    except (OSError, tomllib.TOMLDecodeError):
        return DEFAULT_BACKGROUND_COLOR_HEX
    background_color = theme_colors.get("background")
    if not isinstance(background_color, str) or not HEX_COLOR_PATTERN.fullmatch(
        background_color
    ):
        return DEFAULT_BACKGROUND_COLOR_HEX
    return background_color.lower()


def compose_theme_source_identifier(source_identifier, background_color_hex):
    return f"{source_identifier} theme-background={background_color_hex}"
