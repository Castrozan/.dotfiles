import math
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class VideoError(Exception):
    def __init__(self, category):
        self.category = category
        super().__init__(category)


def validate_operation_id(value):
    try:
        if not isinstance(value, str) or str(uuid.UUID(value)) != value:
            raise ValueError
    except ValueError:
        raise VideoError("invalid_operation_id") from None
    return value


def has_control_character(value: str):
    return any(ord(character) < 32 for character in value)


def validate_attribution(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise VideoError("invalid_attribution")
    if has_control_character(value):
        raise VideoError("invalid_attribution")


def validate_recipe_registration(recipe_registration):
    if (
        not isinstance(recipe_registration, str)
        or "\x00" in recipe_registration
        or not Path(recipe_registration).is_absolute()
    ):
        raise VideoError("invalid_registration_path")


def validate_video_contract(width, height, fps, frames):
    for value, expected in (
        (width, 1080),
        (height, 1920),
        (fps, 30),
        (frames, 1800),
    ):
        if type(value) is not int or value != expected:
            raise VideoError("unsupported_video_contract")


def validate_deadline_seconds(deadline_seconds):
    if (
        type(deadline_seconds) not in (int, float)
        or not math.isfinite(deadline_seconds)
        or not 0 < deadline_seconds <= 600
    ):
        raise VideoError("invalid_deadline")


@dataclass(frozen=True)
class VideoRequest:
    recipe_registration: str
    experiment_id: str
    episode_id: str
    width: int
    height: int
    fps: int
    frames: int
    deadline_seconds: float

    def __post_init__(self):
        validate_attribution(self.experiment_id)
        validate_attribution(self.episode_id)
        validate_recipe_registration(self.recipe_registration)
        validate_video_contract(self.width, self.height, self.fps, self.frames)
        validate_deadline_seconds(self.deadline_seconds)
        object.__setattr__(self, "deadline_seconds", float(self.deadline_seconds))


@dataclass(frozen=True)
class RegisteredFile:
    source_path: Path
    relative_path: str
    sha256: str


@dataclass(frozen=True)
class RegisteredRecipe:
    recipe_id: str
    recipe_directory: Path
    renderer_version: str
    registration: RegisteredFile
    manifest: RegisteredFile
    binary: RegisteredFile
    files: tuple[RegisteredFile, ...]


@dataclass(frozen=True)
class PreparedRecipe:
    binary_path: Path
    recipe_directory: Path


@dataclass(frozen=True)
class VerifiedVideo:
    media: dict
    verification: dict


class VideoRenderProvider(Protocol):
    name: str
    adapter_version: str

    def preflight(self, request: VideoRequest, deadline) -> RegisteredRecipe: ...

    def render(
        self, request: VideoRequest, recipe: PreparedRecipe, directory: Path, deadline
    ) -> VerifiedVideo: ...
