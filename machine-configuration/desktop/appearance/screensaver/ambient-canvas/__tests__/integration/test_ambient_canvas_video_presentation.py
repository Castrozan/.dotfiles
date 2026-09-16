import json
import pathlib
import subprocess
import sys

import pytest

AMBIENT_CANVAS_DIRECTORY = pathlib.Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(
    sys.platform != "darwin", reason="Requires AVFoundation"
)


@pytest.fixture(scope="module")
def video_presentation_test_binary(tmp_path_factory):
    binary_path = tmp_path_factory.mktemp("ambient-canvas") / "video-presentation-test"
    source_paths = sorted((AMBIENT_CANVAS_DIRECTORY / "swift-sources").glob("*.swift"))
    source_paths = [
        path for path in source_paths if path.name != "ambient-canvas-player-main.swift"
    ]
    subprocess.run(
        [
            "/usr/bin/swiftc",
            "-o",
            str(binary_path),
            *map(str, source_paths),
            str(
                pathlib.Path(__file__).with_name(
                    "ambient_canvas_video_presentation.swift"
                )
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return binary_path


@pytest.mark.parametrize("segment_count", [1, 2])
def test_pause_and_resume_preserve_playback_while_reconnecting_presentation(
    video_presentation_test_binary, tmp_path, segment_count
):
    manifest_path = tmp_path / "loop.segments.json"
    manifest_path.write_text(
        json.dumps(
            {
                "segments": [
                    {"file": f"segment-{index}.mp4", "durationSeconds": 30}
                    for index in range(segment_count)
                ]
            }
        )
    )
    completed = subprocess.run(
        [str(video_presentation_test_binary), str(manifest_path)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
