from media_image.contract import ImageRequest, validate_operation_id
from media_movie.contract import (
    ImageSelection,
    MovieError,
    MovieRequest,
    MovieScene,
    NarrationSelection,
)


def require_fields(value, required, optional=()):
    if (
        not isinstance(value, dict)
        or not set(required) <= set(value)
        or set(value) - set(required) - set(optional)
    ):
        raise MovieError("invalid_request")


def read_movie_request(document):
    require_fields(
        document,
        ("experiment_id", "episode_id", "width", "height", "fps", "scenes"),
        ("operation_id",),
    )
    if "operation_id" in document:
        validate_operation_id(document["operation_id"])
    if (
        not isinstance(document["scenes"], list)
        or not 1 <= len(document["scenes"]) <= 24
    ):
        raise MovieError("invalid_scenes")
    scenes = []
    for scene in document["scenes"]:
        require_fields(scene, ("image", "narration"), ("duration_seconds", "motion"))
        image = scene["image"]
        narration = scene["narration"]
        require_fields(
            image, ("provider", "model", "prompt", "aspect_ratio", "quality"), ("seed",)
        )
        require_fields(
            narration,
            ("provider", "model", "text", "voice", "language"),
            ("directions",),
        )
        scenes.append(
            MovieScene(
                ImageSelection(
                    image["provider"],
                    ImageRequest(
                        image["prompt"],
                        image["model"],
                        image["aspect_ratio"],
                        image["quality"],
                        image.get("seed"),
                    ),
                ),
                NarrationSelection(**narration),
                scene.get("duration_seconds"),
                scene.get("motion", "static"),
            )
        )
    return MovieRequest(
        document["experiment_id"],
        document["episode_id"],
        document["width"],
        document["height"],
        document["fps"],
        tuple(scenes),
    )
