import shutil
from pathlib import Path

from media_video.contract import VideoError
from media_video.files import file_digest
from media_video.process import CommandRunner
from media_video.registration import load_recipe_registration
from media_video.verification import verify_video


class FframesRenderer:
    name = "fframes"
    adapter_version = "media-video-1"

    def __init__(self, runner=None):
        self.runner = runner or CommandRunner()
        self.ffmpeg = shutil.which("ffmpeg")
        self.ffprobe = shutil.which("ffprobe")

    def preflight(self, request, deadline):
        if not self.ffmpeg or not self.ffprobe:
            raise VideoError("media_tools_unavailable")
        return load_recipe_registration(Path(request.recipe_registration), deadline)

    def render(self, request, recipe, directory, deadline):
        video_path = directory / "render.mp4"
        self.runner.run(
            "render",
            [recipe.binary_path, "render", "-o", video_path],
            recipe.recipe_directory,
            directory / "logs",
            deadline,
        )
        file_digest(video_path, deadline)
        return verify_video(
            request, directory, self.runner, self.ffmpeg, self.ffprobe, deadline
        )
