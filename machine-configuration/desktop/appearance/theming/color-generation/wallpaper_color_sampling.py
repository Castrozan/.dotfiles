import io
from pathlib import Path

from colorthief import ColorThief
from PIL import Image

COLOR_SAMPLE_MAXIMUM_SIDE_PIXELS = 400


def extract_first_frame_if_gif(image_path: Path, first_frame_path: Path) -> Path:
    with Image.open(image_path) as image:
        if image.format == "GIF":
            image.seek(0)
            image.save(first_frame_path, "PNG")
            return first_frame_path
    return image_path


def extract_dominant_colors_from_image(image_path: Path) -> list[tuple[int, int, int]]:
    with Image.open(image_path) as image:
        color_sample = image.convert("RGB")
    color_sample.thumbnail(
        (COLOR_SAMPLE_MAXIMUM_SIDE_PIXELS, COLOR_SAMPLE_MAXIMUM_SIDE_PIXELS)
    )
    color_sample_png = io.BytesIO()
    color_sample.save(color_sample_png, "PNG")
    color_sample_png.seek(0)
    color_thief = ColorThief(color_sample_png)
    return color_thief.get_palette(color_count=16, quality=1)
