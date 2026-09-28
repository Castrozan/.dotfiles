import json
import os
from pathlib import Path
import subprocess
import sys
import time


MEDIA_SCRIPTS_DIRECTORY = (
    Path(__file__).resolve().parents[2] / "scripts/ambient_canvas_media"
)


def test_launcher_records_missing_assets_before_attempting_display_queries(tmp_path):
    environment = dict(os.environ)
    environment.pop("AMBIENT_CANVAS_INDEX", None)
    completed = subprocess.run(
        [
            sys.executable,
            str(MEDIA_SCRIPTS_DIRECTORY / "ensure_ambient_canvas_screensaver.py"),
            "--output-directory",
            str(tmp_path),
            "--source-identifier",
            "test-source",
            "--theme-colors-path",
            str(tmp_path / "colors.toml"),
        ],
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert completed.returncode == 1
    log = (tmp_path / "launcher.log").read_text()
    assert "launcher_started" in log
    assert "web_assets_missing" in log
    assert "launcher_finished exit_code=1" in log


def test_detached_launch_persists_failure_after_the_launcher_returns(tmp_path):
    player_path = tmp_path / "player"
    player_path.write_text(
        f"#!{sys.executable}\nimport sys\nprint('failed player', file=sys.stderr)\nsys.exit(23)\n"
    )
    player_path.chmod(0o700)
    loop_directory = tmp_path / "loops"
    loop_directory.mkdir()
    (loop_directory / "segment.mp4").write_bytes(b"recorded segment")
    (loop_directory / "loop.segments.json").write_text(
        json.dumps({"segments": [{"file": "segment.mp4"}]})
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from playback.display_ambient_canvas_loop import launch_display; sys.exit(launch_display(*sys.argv[1:]))",
            str(player_path),
            str(loop_directory),
            str(tmp_path / "playback-dwell-seconds"),
        ],
        env={**os.environ, "PYTHONPATH": str(MEDIA_SCRIPTS_DIRECTORY)},
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert completed.returncode == 0, completed.stderr
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        reports = list((tmp_path / "player-runs").glob("*/report.json"))
        if reports:
            report = json.loads(reports[0].read_text())
            if report["status"] == "failed":
                break
        time.sleep(0.05)
    else:
        raise AssertionError("Detached player exit was not reported")
    assert report["exit_code"] == 23
    assert "failed player" in report["output_tail"]
