import hashlib
import json
import math
import subprocess
from urllib.parse import urlparse


REVIEW_DIMENSIONS = (
    "novel_topic",
    "factual_accuracy",
    "opening",
    "payoff",
    "visual_storytelling",
    "voice_performance",
    "caption_readability",
    "sound_mix",
    "full_playback",
)


def command(arguments, timeout=300):
    result = subprocess.run(arguments, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise ValueError(f"Command failed: {arguments[0]}")
    return result.stdout


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def inside_run(run_directory, value):
    path = (run_directory / value).resolve()
    if not path.is_relative_to(run_directory.resolve()) or not path.is_file():
        raise ValueError("Evidence must exist inside the current run")
    return path


def validate_review(run_directory, episode):
    for field, minimum in (("sources", 2), ("references", 3), ("candidates", 3)):
        if len(episode.get(field, [])) < minimum:
            raise ValueError(f"Missing research: {field}")
    for field in ("sources", "references"):
        if len({source["url"] for source in episode[field]}) != len(episode[field]):
            raise ValueError("Research URLs must be distinct")
    for source in episode["sources"] + episode["references"]:
        if (
            urlparse(source["url"]).scheme != "https"
            or len(source["finding"].strip()) < 20
        ):
            raise ValueError("Research requires HTTPS sources and substantive findings")
    if not any(source.get("primary") is True for source in episode["sources"]):
        raise ValueError("At least one primary factual source is required")
    for dimension in REVIEW_DIMENSIONS:
        review = episode.get("review", {}).get(dimension, {})
        if (
            review.get("passed") is not True
            or len(review.get("finding", "").strip()) < 20
        ):
            raise ValueError(f"Quality review incomplete: {dimension}")
        inside_run(run_directory, review["evidence"])
    beats = episode.get("beats", [])
    if not 6 <= len(beats) <= 24:
        raise ValueError("A visual narrative requires 6 to 24 inspected beats")
    for beat in beats:
        inside_run(run_directory, beat["frame"])
    return inside_run(run_directory, episode["video"])


def verify_episode(run_directory, episode):
    video = validate_review(run_directory, episode)
    if video.stat().st_size > 25 * 1024 * 1024:
        raise ValueError("Final video exceeds the browser's 25 MiB upload limit")
    media = json.loads(
        command(
            [
                "ffprobe",
                "-v",
                "error",
                "-count_frames",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(video),
            ]
        )
    )
    videos = [stream for stream in media["streams"] if stream["codec_type"] == "video"]
    audios = [stream for stream in media["streams"] if stream["codec_type"] == "audio"]
    if len(videos) != 1 or len(audios) != 1:
        raise ValueError("Expected one video and one audio stream")
    picture, audio = videos[0], audios[0]
    duration = float(media["format"]["duration"])
    numerator, denominator = map(int, picture["avg_frame_rate"].split("/"))
    if (
        (picture["width"], picture["height"], picture["codec_name"], picture["pix_fmt"])
        != (1080, 1920, "h264", "yuv420p")
        or denominator == 0
        or numerator / denominator != 30
    ):
        raise ValueError("Expected 1080x1920 H264/yuv420p at 30 fps")
    if not math.isfinite(duration) or not 20 <= duration <= 180:
        raise ValueError("Short duration must be between 20 and 180 seconds")
    if audio["codec_name"] != "aac" or int(audio["sample_rate"]) != 48000:
        raise ValueError("Expected AAC at 48 kHz")
    if abs(int(picture["nb_read_frames"]) - duration * 30) > 2:
        raise ValueError("Unexpected decoded frame count")
    command(["ffmpeg", "-v", "error", "-xerror", "-i", str(video), "-f", "null", "-"])
    return {"sha256": digest(video), "duration_seconds": duration, "full_decode": True}


def verify_publication(url, channel_id):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "www.youtube.com":
        raise ValueError("Expected a direct YouTube URL")
    metadata = json.loads(
        command(
            [
                "yt-dlp",
                "--ignore-config",
                "--no-playlist",
                "--skip-download",
                "-J",
                url,
            ],
            timeout=90,
        )
    )
    if (
        metadata.get("channel_id") != channel_id
        or metadata.get("availability") != "public"
    ):
        raise ValueError("Publication must be public on the authorized channel")
    return metadata["id"]
