from pathlib import Path
from tempfile import TemporaryDirectory

from media_movie.contract import MovieAsset, MovieError
from media_movie.asset_responses import asset_error_category, read_asset_response
from media_video.contract import VideoError
from media_video.deadline import ExecutionDeadline
from media_video.process import CommandRunner


class MovieAssetGateway:
    def __init__(
        self,
        image_command,
        speech_command,
        image_state_directory,
        speech_state_directory,
    ):
        self.image_command = image_command
        self.speech_command = speech_command
        self.image_state_directory = image_state_directory
        self.speech_state_directory = speech_state_directory

    def invoke(self, command, state_directory, arguments, text_flag, text):
        with TemporaryDirectory(prefix="media-movie-input-") as temporary:
            directory = Path(temporary).resolve()
            text_path = directory / "input.txt"
            text_path.write_text(text, encoding="utf-8")
            text_path.chmod(0o600)
            logs = directory / "logs"
            try:
                output = CommandRunner().run(
                    "asset",
                    [
                        command,
                        "--state-directory",
                        state_directory,
                        *arguments,
                        text_flag,
                        text_path,
                    ],
                    directory,
                    logs,
                    ExecutionDeadline(210),
                )
            except VideoError as error:
                raise MovieError(
                    asset_error_category(logs / "asset.stderr.log", error.category)
                ) from None
            return read_asset_response(output)

    def image_arguments(self, action, selection, operation_id=None):
        request = selection.request
        arguments = [
            action,
            "--provider",
            selection.provider,
            "--model",
            request.model,
            "--aspect-ratio",
            request.aspect_ratio,
            "--quality",
            request.quality,
        ]
        if request.seed is not None:
            arguments.extend(("--seed", str(request.seed)))
        if operation_id is not None:
            arguments.extend(("--operation-id", operation_id))
        return arguments

    def narration_arguments(self, action, selection, operation_id=None):
        arguments = [
            action,
            "--provider",
            selection.provider,
            "--model",
            selection.model,
            "--voice",
            selection.voice,
            "--language",
            selection.language,
        ]
        if selection.directions is not None:
            arguments.extend(("--directions", selection.directions))
        if operation_id is not None:
            arguments.extend(("--operation-id", operation_id))
        return arguments

    def preflight(self, scene):
        self.invoke(
            self.image_command,
            self.image_state_directory,
            self.image_arguments("validate", scene.image),
            "--prompt-file",
            scene.image.request.prompt,
        )
        self.invoke(
            self.speech_command,
            self.speech_state_directory,
            self.narration_arguments("validate", scene.narration),
            "--text-file",
            scene.narration.text,
        )

    def generate_image(self, operation_id, selection):
        receipt = self.invoke(
            self.image_command,
            self.image_state_directory,
            self.image_arguments("generate", selection, operation_id),
            "--prompt-file",
            selection.request.prompt,
        )
        return MovieAsset(
            self.image_state_directory / operation_id / "image.png",
            receipt["image"]["sha256"],
        )

    def generate_narration(self, operation_id, selection):
        receipt = self.invoke(
            self.speech_command,
            self.speech_state_directory,
            self.narration_arguments("generate", selection, operation_id),
            "--text-file",
            selection.text,
        )
        return MovieAsset(
            self.speech_state_directory / operation_id / "speech.wav",
            receipt["audio"]["sha256"],
            receipt["audio"]["duration_seconds"],
        )
