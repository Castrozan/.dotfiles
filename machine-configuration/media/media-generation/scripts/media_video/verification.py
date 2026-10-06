import json
import math
import struct
from fractions import Fraction

from media_video.contract import VerifiedVideo, VideoError


def read_probe(path):
    if path.stat().st_size > 1024 * 1024:
        raise VideoError("invalid_media_probe")
    try:
        result = json.loads(path.read_bytes())
        if not isinstance(result, dict):
            raise ValueError
    except ValueError:
        raise VideoError("invalid_media_probe") from None
    return result


def validate_probe(probe, request):
    try:
        streams = probe["streams"]
        video_streams = [entry for entry in streams if entry["codec_type"] == "video"]
        audio_streams = [entry for entry in streams if entry["codec_type"] == "audio"]
        if len(video_streams) != 1 or not audio_streams:
            raise ValueError
        video = video_streams[0]
        audio = audio_streams[0]
        frame_count = int(video["nb_read_frames"])
        fps = Fraction(video["avg_frame_rate"])
        video_duration = float(video["duration"])
        container_duration = float(probe["format"]["duration"])
        video_frames = [
            entry for entry in probe["frames"] if entry["media_type"] == "video"
        ]
        expected_duration = request.frames / request.fps
        if (
            video["width"] != request.width
            or video["height"] != request.height
            or fps != request.fps
            or Fraction(video["r_frame_rate"]) != request.fps
            or frame_count != request.frames
            or len(video_frames) != request.frames
            or not math.isclose(video_duration, expected_duration, abs_tol=0.000001)
            or not math.isfinite(container_duration)
            or not expected_duration <= container_duration <= expected_duration + 0.1
            or "mp4" not in probe["format"]["format_name"].split(",")
            or not isinstance(video["codec_name"], str)
            or not isinstance(audio["codec_name"], str)
            or not video["codec_name"]
            or not audio["codec_name"]
            or int(audio["sample_rate"]) <= 0
            or type(audio["channels"]) is not int
            or audio["channels"] <= 0
        ):
            raise ValueError
        for index, frame in enumerate(video_frames):
            if not math.isclose(
                float(frame["best_effort_timestamp_time"]),
                index / request.fps,
                abs_tol=0.000001,
            ):
                raise ValueError
        return {
            "width": video["width"],
            "height": video["height"],
            "fps": {"numerator": fps.numerator, "denominator": fps.denominator},
            "frame_count": frame_count,
            "video_duration_seconds": video_duration,
            "container_duration_seconds": container_duration,
            "video_codec": video["codec_name"],
            "audio_codec": audio["codec_name"],
            "audio_sample_rate_hz": int(audio["sample_rate"]),
            "audio_channels": int(audio["channels"]),
        }
    except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError):
        raise VideoError("video_contract_mismatch") from None


def validate_thumbnail(path, request):
    with path.open("rb") as image:
        header = image.read(24)
    if (
        len(header) != 24
        or header[:8] != b"\x89PNG\r\n\x1a\n"
        or header[12:16] != b"IHDR"
        or struct.unpack(">II", header[16:24]) != (request.width, request.height)
    ):
        raise VideoError("invalid_thumbnail")


def verify_video(request, directory, runner, ffmpeg, ffprobe, deadline):
    video_path = directory / "render.mp4"
    logs = directory / "logs"
    probe_path = runner.run(
        "probe",
        [
            ffprobe,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-show_frames",
            "-count_frames",
            "-show_entries",
            "stream=codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,nb_read_frames,duration,sample_rate,channels:format=duration,format_name:frame=media_type,best_effort_timestamp_time",
            "-of",
            "json",
            video_path,
        ],
        directory,
        logs,
        deadline,
    )
    media = validate_probe(read_probe(probe_path), request)
    runner.run(
        "decode",
        [
            ffmpeg,
            "-v",
            "error",
            "-xerror",
            "-i",
            video_path,
            "-map",
            "0:v:0",
            "-map",
            "0:a",
            "-f",
            "null",
            "-",
        ],
        directory,
        logs,
        deadline,
    )
    thumbnail = directory / "thumbnail.png"
    runner.run(
        "thumbnail",
        [
            ffmpeg,
            "-v",
            "error",
            "-xerror",
            "-n",
            "-ss",
            "1",
            "-i",
            video_path,
            "-frames:v",
            "1",
            "-c:v",
            "png",
            thumbnail,
        ],
        directory,
        logs,
        deadline,
    )
    validate_thumbnail(thumbnail, request)
    deadline.remaining()
    return VerifiedVideo(
        media,
        {
            "all_frame_timestamps": "passed",
            "full_audio_video_decode": "passed",
            "thumbnail": "passed",
        },
    )
