import math
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from media_image.contract import ImageRequest
from media_speech.contract import SpeechRequest
from media_speech.delivery import direct_speech_text


class MovieError(Exception):
    def __init__(self, category):
        self.category = category
        super().__init__(category)


@dataclass(frozen=True)
class ImageSelection:
    provider: str
    request: ImageRequest


@dataclass(frozen=True)
class NarrationSelection:
    provider: str
    model: str
    text: str
    voice: str
    language: str
    directions: str | None = None

    def speech_request(self):
        return SpeechRequest(
            direct_speech_text(self.text, self.provider, self.model, self.directions),
            self.voice,
            self.language,
        )


@dataclass(frozen=True)
class MovieScene:
    image: ImageSelection
    narration: NarrationSelection
    duration_seconds: float | None = None
    motion: str = "static"

    def __post_init__(self):
        if not isinstance(self.image, ImageSelection) or not isinstance(
            self.narration, NarrationSelection
        ):
            raise MovieError("invalid_scene")
        self.narration.speech_request()
        validate_scene_duration(self.duration_seconds)
        if self.motion not in ("static", "zoom_in"):
            raise MovieError("unsupported_motion")


@dataclass(frozen=True)
class MovieRequest:
    experiment_id: str
    episode_id: str
    width: int
    height: int
    fps: int
    scenes: tuple[MovieScene, ...]

    def __post_init__(self):
        validate_movie_attribution(self.experiment_id)
        validate_movie_attribution(self.episode_id)
        validate_movie_format(self.width, self.height, self.fps)
        validate_movie_scenes(self.scenes)
        validate_movie_duration(self.scenes)
        validate_movie_script(self.scenes)


def validate_scene_duration(duration_seconds):
    if duration_seconds is None:
        return
    if type(duration_seconds) not in (int, float):
        raise MovieError("invalid_scene_duration")
    if not math.isfinite(duration_seconds) or not 0 < duration_seconds <= 600:
        raise MovieError("invalid_scene_duration")


def validate_movie_scenes(scenes):
    if not isinstance(scenes, tuple):
        raise MovieError("invalid_scenes")
    if not 1 <= len(scenes) <= 24:
        raise MovieError("invalid_scenes")
    if any(not isinstance(scene, MovieScene) for scene in scenes):
        raise MovieError("invalid_scenes")


def validate_movie_duration(scenes):
    if sum(scene.duration_seconds or 0 for scene in scenes) > 600:
        raise MovieError("movie_duration_limit_exceeded")


def validate_movie_script(scenes):
    if sum(len(scene.narration.speech_request().text) for scene in scenes) > 8000:
        raise MovieError("movie_script_limit_exceeded")


def validate_movie_attribution(value):
    if not isinstance(value, str):
        raise MovieError("invalid_attribution")
    if not 1 <= len(value.strip()) <= 200 or any(
        ord(character) < 32 for character in value
    ):
        raise MovieError("invalid_attribution")


def valid_movie_dimension(value):
    return type(value) is int and 16 <= value <= 1920 and value % 2 == 0


def validate_movie_format(width, height, fps):
    if not all(valid_movie_dimension(value) for value in (width, height)):
        raise MovieError("unsupported_movie_format")
    if type(fps) is not int or fps not in (24, 25, 30):
        raise MovieError("unsupported_movie_format")


@dataclass(frozen=True)
class MovieAsset:
    path: Path
    sha256: str
    duration_seconds: float = 0


@dataclass(frozen=True)
class PreparedMovieScene:
    image: MovieAsset
    narration: MovieAsset
    frames: int
    motion: str


@dataclass(frozen=True)
class MovieRenderSpecification:
    width: int
    height: int
    fps: int
    frames: int


class MovieAssetGenerator(Protocol):
    def preflight(self, scene: MovieScene) -> None: ...

    def generate_image(
        self, operation_id: str, selection: ImageSelection
    ) -> MovieAsset: ...

    def generate_narration(
        self, operation_id: str, selection: NarrationSelection
    ) -> MovieAsset: ...


class MovieAssembler(Protocol):
    name: str

    def preflight(self) -> None: ...

    def assemble(
        self,
        request: MovieRequest,
        scenes: tuple[PreparedMovieScene, ...],
        directory: Path,
    ) -> dict: ...
