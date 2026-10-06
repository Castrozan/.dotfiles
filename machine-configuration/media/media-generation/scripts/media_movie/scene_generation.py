import math
import uuid

from media_movie.asset_files import retain_movie_asset
from media_movie.contract import MovieError, PreparedMovieScene
from media_video.files import atomic_json


def retain_scene_asset(directory, receipt, filename, asset):
    retained = retain_movie_asset(directory, filename, asset)
    receipt["retained_inputs"].append(
        {"filename": retained.path.name, "sha256": retained.sha256}
    )
    atomic_json(directory / "receipt.json", receipt)
    return retained


def prepare_movie_scene(operation_id, index, scene, directory, receipt, assets):
    image_operation = str(uuid.uuid5(uuid.UUID(operation_id), f"scene-{index}-image"))
    narration_operation = str(
        uuid.uuid5(uuid.UUID(operation_id), f"scene-{index}-narration")
    )
    receipt["child_operations"].append(
        {
            "scene": index,
            "image_operation_id": image_operation,
            "speech_operation_id": narration_operation,
        }
    )
    atomic_json(directory / "receipt.json", receipt)
    image = assets.generate_image(image_operation, scene.image)
    image = retain_scene_asset(directory, receipt, f"scene-{index:02}.image.png", image)
    narration = assets.generate_narration(narration_operation, scene.narration)
    if (
        not math.isfinite(narration.duration_seconds)
        or not 0 < narration.duration_seconds <= 600
    ):
        raise MovieError("invalid_narration_duration")
    narration = retain_scene_asset(
        directory, receipt, f"scene-{index:02}.narration.wav", narration
    )
    duration = scene.duration_seconds or narration.duration_seconds
    frames = math.ceil(duration * receipt["request"]["fps"])
    if narration.duration_seconds > frames / receipt["request"]["fps"]:
        raise MovieError("narration_exceeds_scene_duration")
    return PreparedMovieScene(image, narration, frames, scene.motion)


def prepare_movie_scenes(operation_id, request, directory, receipt, assets):
    scenes = tuple(
        prepare_movie_scene(operation_id, index, scene, directory, receipt, assets)
        for index, scene in enumerate(request.scenes)
    )
    if sum(scene.frames for scene in scenes) / request.fps > 600:
        raise MovieError("movie_duration_limit_exceeded")
    return scenes
