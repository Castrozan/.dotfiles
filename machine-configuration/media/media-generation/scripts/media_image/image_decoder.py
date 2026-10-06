import io
import warnings

from PIL import Image, UnidentifiedImageError

from media_image.contract import MAXIMUM_IMAGE_BYTES, GeneratedImage, ImageError


def decode_generated_image(image_bytes, provider_request_id=None, usage=None):
    if (
        not isinstance(image_bytes, bytes)
        or not 1 <= len(image_bytes) <= MAXIMUM_IMAGE_BYTES
    ):
        raise ImageError("invalid_image")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(image_bytes)) as image:
                if image.format != "PNG" or getattr(image, "n_frames", 1) != 1:
                    raise ImageError("invalid_image_format")
                width, height = image.size
                color_mode = image.mode
                if width > 8192 or height > 8192 or width * height > 20_000_000:
                    raise ImageError("invalid_image")
                image.verify()
            with Image.open(io.BytesIO(image_bytes)) as image:
                image.load()
    except (
        UnidentifiedImageError,
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
