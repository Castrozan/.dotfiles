import hashlib
import math
import os
import shutil
import subprocess
import uuid
import wave
from pathlib import Path

import pytest
from PIL import Image

from media_image.contract import ImageRequest
from media_movie.contract import (
    ImageSelection,
    MovieAsset,
    MovieRequest,
    MovieScene,
    NarrationSelection,
)
from media_movie.ffmpeg_assembler import FfmpegMovieAssembler
from media_movie.service import MovieService


class FixtureAssets:
    def __init__(self, directory):
        self.directory = directory
        self.calls = []

    def preflight(self, scene):
        self.calls.append("preflight")

    def generate_image(self, operation_id, selection):
        self.calls.append("image")
        path = self.directory / f"{operation_id}.png"
        Image.new("RGB", (64, 64), selection.request.prompt).save(path)
        return MovieAsset(path, hashlib.sha256(path.read_bytes()).hexdigest())

    def generate_narration(self, operation_id, selection):
        self.calls.append("narration")
        path = self.directory / f"{operation_id}.wav"
        with wave.open(str(path), "wb") as audio:
            audio.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
            audio.writeframes(b"\x00\x10" * 4800)
        return MovieAsset(path, hashlib.sha256(path.read_bytes()).hexdigest(), 0.2)


def fixture_movie(fps):
    scenes = tuple(
        MovieScene(
            ImageSelection(
                "replicate",
                ImageRequest(
                    color, "black-forest-labs/flux-schnell", "1:1", "standard"
                ),
            ),
            NarrationSelection(
                "elevenlabs", "eleven_v4", "Hello.", "voice", "en-us", "calm"
            ),
            duration,
            motion,
        )
        for color, duration, motion in (
            ("red", 0.4, "static"),
            ("blue", 0.8, "zoom_in"),
        )
    )
    return MovieRequest("fixtures", "render", 64, 64, fps, scenes)


@pytest.mark.parametrize("fps", [24, 25, 30])
def test_movie_produces_decodable_mp4_with_exact_timestamps_and_replay(tmp_path, fps):
    ffmpeg = os.environ.get("MEDIA_MOVIE_FFMPEG") or shutil.which("ffmpeg")
    ffprobe = os.environ.get("MEDIA_MOVIE_FFPROBE") or shutil.which("ffprobe")
    assert ffmpeg
    assert ffprobe
    assets = FixtureAssets(tmp_path)
    service = MovieService(
        tmp_path / "state", assets, FfmpegMovieAssembler(ffmpeg, ffprobe)
    )
    operation_id = str(uuid.uuid4())
    request = fixture_movie(fps)
    receipt = service.generate(operation_id, request)
    assert receipt["status"] == "succeeded"
    expected_frames = sum(
        math.ceil(scene.duration_seconds * fps) for scene in request.scenes
    )
    assert receipt["media"]["frame_count"] == expected_frames
    assert receipt["media"]["audio_sample_rate_hz"] == 48000
    assert receipt["media"]["audio_channels"] == 2
    assert set(receipt["verification"].values()) == {"passed"}
    video = Path(receipt["assets"]["video"]["path"])
    for timestamp, channel in ((0.1, 0), (0.9, 2)):
        result = subprocess.run(
            [
                ffmpeg,
                "-v",
                "error",
                "-ss",
                str(timestamp),
                "-i",
                str(video),
                "-frames:v",
                "1",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "-",
            ],
            capture_output=True,
            check=True,
            timeout=30,
        )
        assert result.stdout[channel] > 200
        assert result.stdout[(channel + 1) % 3] < 20
    before = {
        path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in video.parent.rglob("*")
        if path.is_file()
    }
    calls = list(assets.calls)
    assert service.generate(operation_id, request) == receipt
    assert service.inspect(operation_id) == receipt
    assert assets.calls == calls
    assert {
        path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in before
    } == before
