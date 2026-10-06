import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from media_movie.discovery import example_movie_request


ROOT = Path(__file__).resolve().parents[2]


def cli_call(arguments, environment):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/media_movie_cli.py"), *arguments],
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_movie_cli_calls_public_asset_apis_and_returns_finished_mp4(
    tmp_path, operation_id
):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "scripts")
    environment["MEDIA_MOVIE_FFMPEG"] = os.environ.get(
        "MEDIA_MOVIE_FFMPEG"
    ) or shutil.which("ffmpeg")
    environment["MEDIA_MOVIE_FFPROBE"] = os.environ.get(
        "MEDIA_MOVIE_FFPROBE"
    ) or shutil.which("ffprobe")
    for kind, variable in (
        ("image", "MEDIA_IMAGE_COMMAND"),
        ("speech", "MEDIA_SPEECH_COMMAND"),
    ):
        wrapper = tmp_path / f"asset-{kind}"
        wrapper.write_text(
            "#!/bin/sh\nexec "
            + shlex.quote(sys.executable)
            + " "
            + shlex.quote(str(ROOT / "__tests__/fixtures/media_asset_cli.py"))
            + " "
            + kind
            + ' "$@"\n'
        )
        wrapper.chmod(0o700)
        environment[variable] = str(wrapper)
    document = example_movie_request()
    document.update(operation_id=operation_id, width=64, height=64)
    document["scenes"][0]["image"].update(
        provider="openai",
        model="gpt-image-2.5-flare",
        aspect_ratio="1:1",
        quality="low",
    )
    del document["scenes"][0]["image"]["seed"]
    document["scenes"][0]["narration"]["voice"] = "fixtureVoice"
    request_path = tmp_path / "movie.json"
    request_path.write_text(json.dumps(document))
    state = tmp_path / "state"
    arguments = [
        "--state-directory",
        str(state),
        "--image-state-directory",
        str(tmp_path / "images"),
        "--speech-state-directory",
        str(tmp_path / "speech"),
        "generate",
        "--request-file",
        str(request_path),
    ]
    result = cli_call(arguments, environment)
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["status"] == "succeeded"
    assert receipt["media"]["frame_count"] == 6
    assert receipt["media"]["video_codec"] == "h264"
    assert receipt["media"]["audio_codec"] == "aac"
    assert receipt["cost"]["provider_charge_usd"] is None
    child = receipt["child_operations"][0]
    image = json.loads(
        (tmp_path / "images" / child["image_operation_id"] / "receipt.json").read_text()
    )
    speech = json.loads(
        (
            tmp_path / "speech" / child["speech_operation_id"] / "receipt.json"
        ).read_text()
    )
    assert image["provider_request_id"] == "fixture-image"
    assert speech["provider_request_id"] == "fixture-speech"
    assert speech["model"] == "eleven_v4"
    video = Path(receipt["assets"]["video"]["path"])
    assert video.stat().st_mode & 0o777 == 0o600
    before = {
        path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert json.loads(cli_call(arguments, environment).stdout) == receipt
    for variable in (
        "MEDIA_IMAGE_COMMAND",
        "MEDIA_SPEECH_COMMAND",
        "MEDIA_MOVIE_FFMPEG",
        "MEDIA_MOVIE_FFPROBE",
    ):
        del environment[variable]
    inspected = cli_call(
        ["--state-directory", str(state), "inspect", operation_id], environment
    )
    assert inspected.returncode == 0
    assert json.loads(inspected.stdout) == receipt
    assert {
        path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in before
    } == before
