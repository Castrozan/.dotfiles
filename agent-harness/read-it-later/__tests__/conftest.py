import subprocess
import sys
from pathlib import Path

import pytest

COMPONENT_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(COMPONENT_DIRECTORY / "ril_cli"))
sys.path.insert(
    0,
    str(
        COMPONENT_DIRECTORY.parent
        / "agent-instructions"
        / "skills"
        / "development"
        / "forge"
        / "scripts"
    ),
)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ril_test_doubles import (  # noqa: E402
    RecordingForge,
    RecordingLauncher,
    write_sandbox_vault,
)


@pytest.fixture
def write_capture():
    def write(capture_inbox_directory: Path, name: str, body: str) -> Path:
        capture_inbox_directory.mkdir(parents=True, exist_ok=True)
        capture_path = capture_inbox_directory / name
        capture_path.write_text(body, encoding="utf-8")
        return capture_path

    return write


def git(directory: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(directory), *arguments],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    ).stdout.strip()


@pytest.fixture
def repository_with_origin(tmp_path):
    origin = tmp_path / "origin.git"
    checkout = tmp_path / "checkout"
    subprocess.run(
        ["git", "init", "--quiet", "--bare", "-b", "main", str(origin)],
        check=True,
        timeout=60,
    )
    subprocess.run(
        ["git", "clone", "--quiet", str(origin), str(checkout)],
        check=True,
        capture_output=True,
        timeout=60,
    )
    git(checkout, "config", "user.email", "ril@example.invalid")
    git(checkout, "config", "user.name", "ril test")
    git(checkout, "config", "core.hooksPath", "/dev/null")
    (checkout / "README.md").write_text("fixture\n", encoding="utf-8")
    git(checkout, "add", "README.md")
    git(checkout, "commit", "--quiet", "-m", "fixture")
    git(checkout, "push", "--quiet", "origin", "HEAD:refs/heads/main")
    return checkout


@pytest.fixture
def sandbox_vault(tmp_path):
    return write_sandbox_vault(tmp_path / "vault")


@pytest.fixture
def recording_forge():
    return RecordingForge()


@pytest.fixture
def recording_launcher():
    return RecordingLauncher()
