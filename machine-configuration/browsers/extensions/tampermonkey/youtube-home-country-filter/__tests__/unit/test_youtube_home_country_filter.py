from pathlib import Path
import subprocess


def test_youtube_home_country_filter_behavior():
    directory = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            "node",
            "--test",
            str(directory / "country-resolution.test.mjs"),
            str(directory / "homepage-filter.test.mjs"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
