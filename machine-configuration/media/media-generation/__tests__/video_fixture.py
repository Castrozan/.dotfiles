import hashlib
import json
import os
import struct
import tempfile
import threading
from pathlib import Path

from media_video.contract import VideoError, VideoRequest
from media_video.fframes import FframesRenderer


SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[1] / "scripts"


def private_write(path, content):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_bytes(content)
    os.chmod(path, 0o600)


def write_json(path, document):
    private_write(path, json.dumps(document).encode())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe_document():
    return {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1080,
                "height": 1920,
                "avg_frame_rate": "30/1",
                "r_frame_rate": "30/1",
                "nb_read_frames": "1800",
                "duration": "60.000000",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "channels": 2,
            },
        ],
        "format": {"duration": "60.053333", "format_name": "mov,mp4,m4a,3gp,3g2,mj2"},
        "frames": [
            {"media_type": "video", "best_effort_timestamp_time": str(index / 30)}
            for index in range(1800)
        ],
    }


class FixtureCommands:
    def __init__(self):
        self.calls = []
        self.failure = None
        self.entered = threading.Event()
        self.release = None
        self.probe = probe_document()

    def run(self, step, arguments, working_directory, logs_directory, deadline):
        self.calls.append((step, list(arguments), working_directory))
        self.entered.set()
        logs_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        output = logs_directory / f"{step}.stdout.log"
        private_write(output, b"bounded fixture output\n")
        private_write(logs_directory / f"{step}.stderr.log", b"")
        if step == "render":
            private_write(Path(arguments[-1]), b"fixture MP4 bytes, no media encoded")
            if self.release is not None and not self.release.wait(timeout=1):
                raise VideoError("fixture_wait_expired")
        if self.failure == step:
            raise VideoError(f"{step}_failed")
        if step == "probe":
            write_json(output, self.probe)
        if step == "thumbnail":
            private_write(
                Path(arguments[-1]),
                b"\x89PNG\r\n\x1a\n"
                + struct.pack(">I", 13)
                + b"IHDR"
                + struct.pack(">II", 1080, 1920),
            )
        deadline.remaining()
        return output


class FixtureRecipe:
    def __init__(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.recipe = self.root / "recipe"
        self.recipe.mkdir(mode=0o700)
        self.asset = self.recipe / "narration.wav"
        self.source = self.recipe / "main.rs"
        private_write(self.asset, b"owned source audio fixture")
        private_write(self.source, b"fn main() {}")
        self.binary = self.recipe / "compiled-renderer"
        private_write(self.binary, b"\xcf\xfa\xed\xfe" + b"native-header fixture")
        os.chmod(self.binary, 0o700)
        self.manifest = self.recipe / "source-assets.json"
        self.registration = self.root / "registration.json"
        self.refresh()
        self.commands = FixtureCommands()
        self.renderer = FframesRenderer(self.commands)
        self.renderer.ffmpeg = "/fixture/ffmpeg"
        self.renderer.ffprobe = "/fixture/ffprobe"
        self.request = VideoRequest(
            str(self.registration), "experiment", "episode", 1080, 1920, 30, 1800, 10
        )
        self.state = self.root / "state"

    def refresh(self):
        write_json(
            self.manifest,
            {
                "files": [
                    {"path": path.name, "sha256": digest(path)}
                    for path in (self.asset, self.source)
                ]
            },
        )
        write_json(
            self.registration,
            {
                "recipe_id": "fixture",
                "recipe_directory": str(self.recipe),
                "renderer_version": "fixture-only",
                "binary": {"path": str(self.binary), "sha256": digest(self.binary)},
                "source_assets_manifest": {
                    "path": str(self.manifest),
                    "sha256": digest(self.manifest),
                },
            },
        )

    def cleanup(self):
        self.temporary.cleanup()
