import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("hex_color", "expected_accent"),
    [
        ("000000", -1),
        ("ffffff", -1),
        ("808080", -1),
        ("fff0f0", -1),
        ("100000", 0),
        ("ff0000", 0),
        ("ff8000", 1),
        ("ffff00", 2),
        ("00ff00", 3),
        ("0000ff", 4),
        ("8000ff", 5),
        ("ff00ff", 6),
    ],
)
def test_accent_uses_hsv_saturation(hex_color, expected_accent):
    script = (
        Path(__file__).resolve().parents[2]
        / "macos/scripts/macos-accent-color-from-hex.py"
    )
    result = subprocess.run(
        [sys.executable, str(script), hex_color],
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    )
    assert result.stdout.strip() == str(expected_accent)
    assert not result.stderr
