import colorsys

ACCENT_LIGHTNESS_STEP_WHILE_LIFTING_FOR_CONTRAST = 0.02


def calculate_yiq_luminance(red: int, green: int, blue: int) -> float:
    return (red * 299 + green * 587 + blue * 114) / 1000


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


def saturate_and_brighten_color(
    color: tuple[int, int, int],
    saturation_boost: float,
    target_lightness: float,
) -> tuple[int, int, int]:
    hue, lightness, saturation = color_to_hls(color)
    boosted_saturation = min(1.0, saturation + (1.0 - saturation) * saturation_boost)
    adjusted_lightness = lightness + (target_lightness - lightness) * 0.7
    return hls_to_color(hue, adjusted_lightness, boosted_saturation)


def calculate_hls_saturation(color: tuple[int, int, int]) -> float:
    return color_to_hls(color)[2]


def format_rgb_as_hex_string(color: tuple[int, int, int]) -> str:
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


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
