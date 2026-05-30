import sys
from pathlib import Path

from colorthief import ColorThief
from PIL import Image
from wallpaper_color_math import (
    calculate_hls_saturation,
    calculate_yiq_luminance,
    color_to_hls,
    darken_color_by_percentage,
    format_rgb_as_hex_string,
    hue_distance,
    lighten_color_by_percentage,
    lighten_color_until_minimum_contrast,
    saturate_and_brighten_color,
)

ANSI_HUE_TARGETS = {
    1: 0.0,
    2: 0.333,
    3: 0.167,
    4: 0.667,
    5: 0.833,
    6: 0.500,
}

MINIMUM_ACCENT_CONTRAST_RATIO = 4.5


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


def sort_colors_by_luminance(
    colors: list[tuple[int, int, int]],
) -> list[tuple[int, int, int]]:
    return sorted(colors, key=lambda rgb: calculate_yiq_luminance(*rgb))


def find_closest_color_by_hue(
    target_hue: float,
    candidate_colors: list[tuple[int, int, int]],
) -> tuple[int, int, int]:
    return min(
        candidate_colors, key=lambda c: hue_distance(color_to_hls(c)[0], target_hue)
    )


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
