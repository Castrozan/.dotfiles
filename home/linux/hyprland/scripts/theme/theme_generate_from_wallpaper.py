import colorsys
import sys
from pathlib import Path

from colorthief import ColorThief
from PIL import Image

ANSI_HUE_TARGETS = {
    1: 0.0,
    2: 0.333,
    3: 0.167,
    4: 0.667,
    5: 0.833,
    6: 0.500,
}

MINIMUM_ACCENT_CONTRAST_RATIO = 4.5
ACCENT_LIGHTNESS_STEP_WHILE_LIFTING_FOR_CONTRAST = 0.02


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
    return color_thief.get_palette(color_count=16, quality=1)


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


def color_to_hls(color: tuple[int, int, int]) -> tuple[float, float, float]:
    return colorsys.rgb_to_hls(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)


def hls_to_color(
    hue: float, lightness: float, saturation: float
) -> tuple[int, int, int]:
    red, green, blue = colorsys.hls_to_rgb(hue, lightness, saturation)
    return (int(red * 255), int(green * 255), int(blue * 255))


def hue_distance(hue_a: float, hue_b: float) -> float:
    diff = abs(hue_a - hue_b)
    return min(diff, 1.0 - diff)


def find_closest_color_by_hue(
    target_hue: float,
    candidate_colors: list[tuple[int, int, int]],
) -> tuple[int, int, int]:
    return min(
        candidate_colors, key=lambda c: hue_distance(color_to_hls(c)[0], target_hue)
    )


def saturate_and_brighten_color(
    color: tuple[int, int, int],
    saturation_boost: float,
    target_lightness: float,
) -> tuple[int, int, int]:
    hue, lightness, saturation = color_to_hls(color)
    boosted_saturation = min(1.0, saturation + (1.0 - saturation) * saturation_boost)
    adjusted_lightness = lightness + (target_lightness - lightness) * 0.7
    return hls_to_color(hue, adjusted_lightness, boosted_saturation)


def linearize_srgb_channel(channel_value: int) -> float:
    normalized = channel_value / 255.0
    if normalized <= 0.03928:
        return normalized / 12.92
    return ((normalized + 0.055) / 1.055) ** 2.4


def calculate_relative_luminance(color: tuple[int, int, int]) -> float:
    red, green, blue = (linearize_srgb_channel(channel) for channel in color)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def calculate_contrast_ratio(
    color_a: tuple[int, int, int], color_b: tuple[int, int, int]
) -> float:
    luminance_a = calculate_relative_luminance(color_a)
    luminance_b = calculate_relative_luminance(color_b)
    lighter = max(luminance_a, luminance_b)
    darker = min(luminance_a, luminance_b)
    return (lighter + 0.05) / (darker + 0.05)


def lighten_color_until_minimum_contrast(
    color: tuple[int, int, int],
    background: tuple[int, int, int],
    minimum_ratio: float,
) -> tuple[int, int, int]:
    hue, lightness, saturation = color_to_hls(color)
    lifted_color = color
    while (
        calculate_contrast_ratio(lifted_color, background) < minimum_ratio
        and lightness < 1.0
    ):
        lightness = min(
            1.0, lightness + ACCENT_LIGHTNESS_STEP_WHILE_LIFTING_FOR_CONTRAST
        )
        lifted_color = hls_to_color(hue, lightness, saturation)
    return lifted_color


def lift_accent_slots_to_minimum_contrast(
    palette: list[tuple[int, int, int]],
    background: tuple[int, int, int],
) -> None:
    for normal_slot in ANSI_HUE_TARGETS:
        bright_slot = normal_slot + 8
        palette[normal_slot] = lighten_color_until_minimum_contrast(
            palette[normal_slot], background, MINIMUM_ACCENT_CONTRAST_RATIO
        )
        palette[bright_slot] = lighten_color_until_minimum_contrast(
            palette[bright_slot], background, MINIMUM_ACCENT_CONTRAST_RATIO
        )
        normal_luminance = calculate_yiq_luminance(*palette[normal_slot])
        bright_luminance = calculate_yiq_luminance(*palette[bright_slot])
        if bright_luminance < normal_luminance:
            palette[bright_slot] = palette[normal_slot]


def assign_colors_to_ansi_slots_by_hue(
    extracted_colors: list[tuple[int, int, int]],
) -> dict[int, tuple[int, int, int]]:
    chromatic_colors = [c for c in extracted_colors if color_to_hls(c)[2] > 0.05]
    if not chromatic_colors:
        chromatic_colors = list(extracted_colors)

    assigned = {}
    for ansi_slot, target_hue in ANSI_HUE_TARGETS.items():
        assigned[ansi_slot] = find_closest_color_by_hue(target_hue, chromatic_colors)

    return assigned


def build_sixteen_color_palette(
    sorted_colors: list[tuple[int, int, int]],
) -> list[tuple[int, int, int]]:
    palette = [sorted_colors[0]] * 16

    palette[0] = darken_color_by_percentage(sorted_colors[0], 0.2)
    palette[7] = lighten_color_by_percentage(sorted_colors[-1], 0.80)
    palette[8] = lighten_color_by_percentage(palette[0], 0.30)
    palette[15] = lighten_color_by_percentage(sorted_colors[-1], 0.90)

    hue_assigned = assign_colors_to_ansi_slots_by_hue(sorted_colors)

    for ansi_slot, base_color in hue_assigned.items():
        palette[ansi_slot] = saturate_and_brighten_color(
            base_color, saturation_boost=0.6, target_lightness=0.45
        )
        palette[ansi_slot + 8] = saturate_and_brighten_color(
            base_color, saturation_boost=0.8, target_lightness=0.55
        )

    lift_accent_slots_to_minimum_contrast(palette, palette[0])

    return palette


def format_rgb_as_hex_string(color: tuple[int, int, int]) -> str:
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def calculate_hls_saturation(color: tuple[int, int, int]) -> float:
    return color_to_hls(color)[2]


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
