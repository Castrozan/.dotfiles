import math
import uuid
from dataclasses import dataclass
from typing import Callable, Protocol

MAXIMUM_PROMPT_CHARACTERS = 8000
MAXIMUM_IMAGE_BYTES = 32 * 1024 * 1024
SUPPORTED_ASPECT_RATIOS = ("1:1", "2:3", "3:2", "9:16", "16:9")


class ImageError(Exception):
    def __init__(self, category):
        self.category = category
        super().__init__(category)


def validate_operation_id(operation_id):
    try:
        if str(uuid.UUID(operation_id)) != operation_id:
            raise ValueError
    except (ValueError, TypeError, AttributeError):
        raise ImageError("invalid_operation_id") from None


@dataclass(frozen=True)
class ImageRequest:
    prompt: str
    model: str
    aspect_ratio: str
    quality: str
    seed: int | None = None

    def __post_init__(self):
        validate_prompt(self.prompt)
        validate_seed(self.seed)
        validate_image_model(self.model)
        if self.aspect_ratio not in SUPPORTED_ASPECT_RATIOS:
            raise ImageError("unsupported_aspect_ratio")
        validate_image_quality(self.quality)


@dataclass(frozen=True)
class GeneratedImage:
    image_bytes: bytes
    width: int
    height: int
    color_mode: str
    provider_request_id: str | None = None
    usage: dict | None = None

    def __post_init__(self):
        validate_image_bytes(self.image_bytes)
        validate_image_dimensions(self.width, self.height)
        if self.color_mode not in (
            "RGB",
            "RGBA",
            "L",
            "LA",
            "P",
        ):
            raise ImageError("invalid_image")
        validate_usage(self.usage)


def validate_image_model(model):
    if not isinstance(model, str) or not 1 <= len(model) <= 100:
        raise ImageError("invalid_model")


def validate_image_quality(quality):
    if not isinstance(quality, str) or not 1 <= len(quality) <= 20:
        raise ImageError("invalid_quality")


def validate_image_bytes(image_bytes):
    if (
        not isinstance(image_bytes, bytes)
        or not 1 <= len(image_bytes) <= MAXIMUM_IMAGE_BYTES
    ):
        raise ImageError("invalid_image")


def validate_image_dimensions(width, height):
    if any(
        type(value) is not int or not 1 <= value <= 8192 for value in (width, height)
    ):
        raise ImageError("invalid_image_dimensions")
    if width * height > 20_000_000:
        raise ImageError("invalid_image")


def validate_prompt(prompt):
    if not isinstance(prompt, str):
        raise ImageError("invalid_prompt")
    if not prompt.strip() or len(prompt) > MAXIMUM_PROMPT_CHARACTERS:
        raise ImageError("invalid_prompt")
    validate_prompt_characters(prompt)


def validate_prompt_characters(prompt):
    if any(ord(character) < 32 and character not in "\n\t" for character in prompt):
        raise ImageError("invalid_prompt")


def validate_seed(seed):
    if seed is None:
        return
    if type(seed) is not int or not 0 <= seed <= 2147483647:
        raise ImageError("invalid_seed")


def validate_usage(usage):
    if usage is None:
        return
    if not isinstance(usage, dict):
        raise ImageError("invalid_usage")
    for key, value in usage.items():
        validate_usage_metric(key, value)


def validate_usage_metric(key, value):
    if any((not isinstance(key, str), type(value) not in (int, float))):
        raise ImageError("invalid_usage")
    if not math.isfinite(value) or value < 0:
        raise ImageError("invalid_usage")


class ImageGenerationProvider(Protocol):
    name: str

    def preflight(self, request: ImageRequest) -> None: ...

    def generate(
        self, request: ImageRequest, record_submission: Callable[[str], None]
    ) -> GeneratedImage: ...
