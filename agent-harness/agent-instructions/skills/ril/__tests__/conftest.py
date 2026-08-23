import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "ril_cli"))


@pytest.fixture
def write_capture():
    def write(capture_inbox_directory: Path, name: str, body: str) -> Path:
        capture_inbox_directory.mkdir(parents=True, exist_ok=True)
        capture_path = capture_inbox_directory / name
        capture_path.write_text(body, encoding="utf-8")
        return capture_path

    return write
