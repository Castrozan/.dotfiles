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
        for value in (self.experiment_id, self.episode_id):
            if not isinstance(value, str) or not value.strip() or len(value) > 200:
                raise VideoError("invalid_attribution")
            if any(ord(character) < 32 for character in value):
                raise VideoError("invalid_attribution")
        if (
            not isinstance(self.recipe_registration, str)
            or "\x00" in self.recipe_registration
            or not Path(self.recipe_registration).is_absolute()
        ):
            raise VideoError("invalid_registration_path")
        for value, expected in (
            (self.width, 1080),
            (self.height, 1920),
            (self.fps, 30),
            (self.frames, 1800),
        ):
            if type(value) is not int or value != expected:
                raise VideoError("unsupported_video_contract")
        if (
            type(self.deadline_seconds) not in (int, float)
            or not math.isfinite(self.deadline_seconds)
            or not 0 < self.deadline_seconds <= 600
        ):
            raise VideoError("invalid_deadline")
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
