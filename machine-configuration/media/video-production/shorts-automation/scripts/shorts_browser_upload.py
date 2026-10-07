import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from shorts_store import read_document


def profile_upload_sandbox(profile_id):
    if not re.fullmatch(r"prof_[a-f0-9]{8}", profile_id):
        raise ValueError("Upload requires a registered profile ID")
    profile_state = Path.home() / ".pinchtab/profiles" / profile_id / ".pinchtab-state"
    runtime = read_document(profile_state / "config.json")
    if Path(runtime["server"]["stateDir"]).resolve() != profile_state.resolve():
        raise ValueError("Upload staging must use the authorized profile's state")
    return profile_state / "uploads"


def upload_video(arguments, server, profile_id):
    parser = argparse.ArgumentParser(prog="shorts-browser upload")
    parser.add_argument("video", type=Path)
    parser.add_argument("--tab", required=True)
    parser.add_argument("--selector", default="input[type=file]")
    options = parser.parse_args(arguments)
    video = options.video.resolve(strict=True)
    if video.suffix.lower() != ".mp4" or not video.is_file():
        raise ValueError("Upload an existing MP4 video")
    if video.stat().st_size > 25 * 1024 * 1024:
        raise ValueError("The video exceeds PinchTab's 25 MiB upload limit")
    configuration = read_document(Path.home() / ".pinchtab/config.json")
    sandbox = profile_upload_sandbox(profile_id)
    sandbox.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory = Path(tempfile.mkdtemp(prefix="pinchtab-upload-shorts-", dir=sandbox))
    destination = directory / "video.mp4"
    shutil.copyfile(video, destination)
    destination.chmod(0o600)
    payload = {
        "selector": options.selector,
        "paths": [str(destination.relative_to(sandbox))],
    }
    request = Request(
        f"{server}/upload?{urlencode({'tabId': options.tab})}",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {configuration['server']['token']}",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
    except Exception as error:
        raise RuntimeError(
            f"Upload result is ambiguous; inspect tab {options.tab}; "
            f"staged file retained at {destination}"
        ) from error
    return dict(result, staged_file=str(destination))
