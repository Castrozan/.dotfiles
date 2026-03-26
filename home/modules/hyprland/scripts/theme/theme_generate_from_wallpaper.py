import colorsys
import sys
from pathlib import Path

from colorthief import ColorThief
from PIL import Image


def extract_first_frame_if_gif(image_path: Path) -> Path:
    with Image.open(image_path) as image:
        if image.format == "GIF":
            first_frame_path = Path("/tmp/wallpaper_first_frame.png")
            image.seek(0)
            image.save(first_frame_path, "PNG")
            return first_frame_path
    return image_path


def extract_dominant_colors_from_image(image_path: Path) -> list[tuple[int, int, int]]:
    color_thief = ColorThief(str(image_path))
    return color_thief.get_palette(color_count=8, quality=1)


def calculate_yiq_luminance(red: int, green: int, blue: int) -> float:
    return (red * 299 + green * 587 + blue * 114) / 1000


def sort_colors_by_luminance(
    colors: list[tuple[int, int, int]],
) -> list[tuple[int, int, int]]:
    return sorted(colors, key=lambda rgb: calculate_yiq_luminance(*rgb))


def darken_color_by_percentage(
    color: tuple[int, int, int], percentage: float
) -> tuple[int, int, int]:
    return (
        int(color[0] * percentage),
        int(color[1] * percentage),
        int(color[2] * percentage),
    )


def lighten_color_by_percentage(
    color: tuple[int, int, int], percentage: float
) -> tuple[int, int, int]:
    return (
        int(color[0] + (255 - color[0]) * percentage),
        int(color[1] + (255 - color[1]) * percentage),
        int(color[2] + (255 - color[2]) * percentage),
    )


def saturate_color(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    red_normalized = color[0] / 255.0
    green_normalized = color[1] / 255.0
    blue_normalized = color[2] / 255.0
    hue, lightness, saturation = colorsys.rgb_to_hls(
        red_normalized, green_normalized, blue_normalized
    )
    boosted_saturation = min(1.0, saturation + (1.0 - saturation) * amount)
    boosted_lightness = max(0.25, min(0.65, lightness))
    red_out, green_out, blue_out = colorsys.hls_to_rgb(
        hue, boosted_lightness, boosted_saturation
    )
    return (
        int(red_out * 255),
        int(green_out * 255),
        int(blue_out * 255),
    )


def pad_color_list_to_eight(
    colors: list[tuple[int, int, int]],
) -> list[tuple[int, int, int]]:
    padded = list(colors)
    while len(padded) < 8:
        padded.append(padded[len(padded) % len(colors)])
    return padded[:8]


def build_sixteen_color_palette(
    sorted_colors: list[tuple[int, int, int]],
) -> list[tuple[int, int, int]]:
    eight_colors = pad_color_list_to_eight(sorted_colors)
    palette = eight_colors + eight_colors

    palette[0] = darken_color_by_percentage(eight_colors[0], 0.2)
    palette[7] = lighten_color_by_percentage(eight_colors[-1], 0.60)
    palette[8] = lighten_color_by_percentage(palette[0], 0.25)
    palette[15] = lighten_color_by_percentage(eight_colors[-1], 0.75)

    for index in [1, 2, 3, 4, 5, 6]:
        palette[index] = saturate_color(eight_colors[index], 0.5)

    for index in [9, 10, 11, 12, 13, 14]:
        palette[index] = saturate_color(eight_colors[index - 8], 0.7)

    return palette


def format_rgb_as_hex_string(color: tuple[int, int, int]) -> str:
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def calculate_hls_saturation(color: tuple[int, int, int]) -> float:
    normalized_red = color[0] / 255.0
    normalized_green = color[1] / 255.0
    normalized_blue = color[2] / 255.0
    _hue, _lightness, saturation = colorsys.rgb_to_hls(
        normalized_red, normalized_green, normalized_blue
    )
    return saturation


def pick_most_saturated_accent_color(
    palette: list[tuple[int, int, int]],
) -> tuple[int, int, int]:
    accent_candidates = palette[1:7]
    return max(accent_candidates, key=calculate_hls_saturation)


def generate_colors_toml_from_palette(palette: list[tuple[int, int, int]]) -> str:
    background = palette[0]
    foreground = palette[7]
    accent = pick_most_saturated_accent_color(palette)

    lines = [
        f'accent = "{format_rgb_as_hex_string(accent)}"',
        f'cursor = "{format_rgb_as_hex_string(foreground)}"',
        f'foreground = "{format_rgb_as_hex_string(foreground)}"',
        f'background = "{format_rgb_as_hex_string(background)}"',
        f'selection_foreground = "{format_rgb_as_hex_string(background)}"',
        f'selection_background = "{format_rgb_as_hex_string(foreground)}"',
        "",
    ]

    for index in range(16):
        lines.append(f'color{index} = "{format_rgb_as_hex_string(palette[index])}"')

    return "\n".join(lines) + "\n"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: theme-generate-from-wallpaper <image-path>", file=sys.stderr)
        raise SystemExit(1)

    wallpaper_image_path = Path(sys.argv[1])
    if not wallpaper_image_path.is_file():
        print(f"Image file not found: {wallpaper_image_path}", file=sys.stderr)
        raise SystemExit(1)

    resolved_image_path = extract_first_frame_if_gif(wallpaper_image_path)
    dominant_colors = extract_dominant_colors_from_image(resolved_image_path)
    luminance_sorted_colors = sort_colors_by_luminance(dominant_colors)
    sixteen_color_palette = build_sixteen_color_palette(luminance_sorted_colors)
    colors_toml_content = generate_colors_toml_from_palette(sixteen_color_palette)
    print(colors_toml_content, end="")


if __name__ == "__main__":
    main()
