import os
from pathlib import Path

from media_movie.contract import MovieError, MovieRenderSpecification
from media_video.deadline import ExecutionDeadline
from media_video.process import CommandRunner
from media_video.verification import verify_video


def scene_filter(request, scene):
    scale = f"scale={request.width}:{request.height}:force_original_aspect_ratio=increase,crop={request.width}:{request.height},setsar=1"
    if scene.motion == "zoom_in":
        scale += f",zoompan=z='min(1+on*0.0005,1.08)':d=1:s={request.width}x{request.height}:fps={request.fps}"
    return scale + f",trim=end_frame={scene.frames},setpts=N/({request.fps}*TB)"


def assembly_arguments(ffmpeg, request, scenes, directory):
    arguments = [ffmpeg, "-nostdin", "-v", "error", "-filter_complex_threads", "2"]
    filters = []
    for index, scene in enumerate(scenes):
        arguments.extend(
            [
                "-framerate",
                str(request.fps),
                "-loop",
                "1",
                "-i",
                scene.image.path,
                "-i",
                scene.narration.path,
            ]
        )
        filters.append(f"[{index * 2}:v]{scene_filter(request, scene)}[video{index}]")
        filters.append(
            f"[{index * 2 + 1}:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={scene.frames / request.fps},asetpts=N/SR/TB[audio{index}]"
        )
    inputs = "".join(f"[video{index}][audio{index}]" for index in range(len(scenes)))
    filters.append(f"{inputs}concat=n={len(scenes)}:v=1:a=1[concatenated][audio]")
    filters.append(f"[concatenated]setpts=N/({request.fps}*TB)[video]")
    arguments.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[video]",
            "-map",
            "[audio]",
            "-r",
            str(request.fps),
            "-t",
            str(sum(scene.frames for scene in scenes) / request.fps),
            "-frames:v",
            str(sum(scene.frames for scene in scenes)),
            "-c:v",
            "libx264",
            "-threads",
            "2",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            directory / "render.mp4",
        ]
    )
    return arguments


class FfmpegMovieAssembler:
    name = "ffmpeg"

    def __init__(self, ffmpeg, ffprobe):
        self.ffmpeg = ffmpeg
        self.ffprobe = ffprobe

    def preflight(self):
        if any(
            not Path(binary).is_file() or not os.access(binary, os.X_OK)
            for binary in (self.ffmpeg, self.ffprobe)
        ):
            raise MovieError("movie_runtime_unavailable")

    def assemble(self, request, scenes, directory):
        runner = CommandRunner()
        deadline = ExecutionDeadline(600)
        runner.run(
            "assembly",
            assembly_arguments(self.ffmpeg, request, scenes, directory),
            directory,
            directory / "logs",
            deadline,
        )
        specification = MovieRenderSpecification(
            request.width,
            request.height,
            request.fps,
            sum(scene.frames for scene in scenes),
        )
        result = verify_video(
            specification, directory, runner, self.ffmpeg, self.ffprobe, deadline
        )
        if (
            result.media["video_codec"] != "h264"
            or result.media["audio_codec"] != "aac"
        ):
            raise MovieError("movie_codec_mismatch")
        return {"media": result.media, "verification": result.verification}
