import pytest

from media_image.contract import ImageRequest
from media_movie.contract import (
    ImageSelection,
    MovieError,
    MovieRequest,
    MovieScene,
    NarrationSelection,
)


def movie_scene(directions=None, provider="elevenlabs", model="eleven_v4"):
    return MovieScene(
        ImageSelection(
            "replicate",
            ImageRequest(
                "A mountain", "black-forest-labs/flux-schnell", "9:16", "standard"
            ),
        ),
        NarrationSelection(
            provider, model, "Hello Lucas.", "voice", "en-us", directions
        ),
        2,
        "zoom_in",
    )


def test_movie_request_carries_real_scene_and_delivery_inputs():
    request = MovieRequest(
        "shorts", "example", 1080, 1920, 30, (movie_scene("curious, then whispers"),)
    )
    assert request.scenes[0].narration.directions == "curious, then whispers"
    assert request.scenes[0].motion == "zoom_in"


@pytest.mark.parametrize(
    "width,height,fps",
    [(0, 1920, 30), (1081, 1920, 30), (1080, 1920, 0), (4096, 4096, 30)],
)
def test_unsupported_movie_format_fails_before_generation(width, height, fps):
    scenes = (movie_scene(),)
    with pytest.raises(MovieError, match="unsupported_movie_format"):
        MovieRequest("shorts", "example", width, height, fps, scenes)


def test_empty_movie_is_rejected():
    with pytest.raises(MovieError, match="invalid_scenes"):
        MovieRequest("shorts", "example", 1080, 1920, 30, ())


def test_unsupported_motion_is_rejected():
    scene = movie_scene()
    with pytest.raises(MovieError, match="unsupported_motion"):
        MovieScene(scene.image, scene.narration, 2, "invented_camera")
