import argparse
import json
import subprocess
from pathlib import Path


def upload_video(arguments, command, environment):
    parser = argparse.ArgumentParser(prog="shorts-browser upload")
    parser.add_argument("video", type=Path)
    parser.add_argument("--tab", required=True)
    parser.add_argument("--selector", default="input[type=file]")
    options = parser.parse_args(arguments)
    video = options.video.resolve(strict=True)
    if video.suffix.lower() != ".mp4" or not video.is_file():
        raise ValueError("Upload an existing MP4 video")
    if video.stat().st_size > 25 * 1024 * 1024:
        raise ValueError("The video exceeds the Shorts 25 MiB upload budget")
    result = subprocess.run(
        [*command, "upload", options.selector, str(video), "--tab", options.tab],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
    )
    return json.loads(result.stdout)["data"]
