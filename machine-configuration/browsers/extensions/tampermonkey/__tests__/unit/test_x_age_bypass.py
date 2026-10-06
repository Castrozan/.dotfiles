from pathlib import Path
import subprocess


def test_x_age_bypass_responses_and_traversal():
    directory = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["node", "--test", str(directory / "x-age-bypass.test.mjs")],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
