import io
import warnings

from PIL import Image

from media_image.contract import GeneratedImage, ImageError, validate_image_bytes


def decode_generated_image(image_bytes, provider_request_id=None, usage=None):
    validate_image_bytes(image_bytes)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(image_bytes)) as image:
                validate_png_header(image)
                width, height = image.size
                color_mode = image.mode
                image.verify()
            with Image.open(io.BytesIO(image_bytes)) as image:
                image.load()
    except (
        OSError,
        ValueError,
        SyntaxError,
        Image.DecompressionBombWarning,
        Image.DecompressionBombError,
    ):
        raise ImageError("invalid_image") from None
    return GeneratedImage(
        image_bytes, width, height, color_mode, provider_request_id, usage
    )


def validate_png_header(image):
    if image.format != "PNG" or getattr(image, "n_frames", 1) != 1:
        raise ImageError("invalid_image_format")
    validate_png_dimensions(*image.size)


def validate_png_dimensions(width, height):
    if width > 8192 or height > 8192 or width * height > 20_000_000:
        raise ImageError("invalid_image")
