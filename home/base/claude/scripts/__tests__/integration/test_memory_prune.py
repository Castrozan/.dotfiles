import subprocess
import sys
from pathlib import Path

import pytest

import memory_prune

WRITE_SCRIPT_PATH = Path(__file__).resolve().parent.parent.parent / "memory-write"
PRUNE_SCRIPT_PATH = Path(__file__).resolve().parent.parent.parent / "memory-prune"


# --------------------------------------------------------------------------- #
# Integration: invoke memory-prune as a subprocess in a temp HOME.            #
# --------------------------------------------------------------------------- #


@pytest.fixture
def isolated_environment(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    return fake_home, workspace


def expected_memory_directory(fake_home: Path, workspace: Path) -> Path:
    encoded = str(workspace).replace("/", "-").replace(".", "-")
    return fake_home / ".claude" / "projects" / encoded / "memory"


def invoke_memory_write(workspace: Path, **arguments) -> subprocess.CompletedProcess:
    command = [sys.executable, str(WRITE_SCRIPT_PATH)]
    for key, value in arguments.items():
        if value is None:
            continue
        command.extend([f"--{key.replace('_', '-')}", value])
    return subprocess.run(
        command,
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=5,
    )


def invoke_memory_prune(workspace: Path, **arguments) -> subprocess.CompletedProcess:
    command = [sys.executable, str(PRUNE_SCRIPT_PATH)]
    for key, value in arguments.items():
        if value is None:
            continue
        command.extend([f"--{key.replace('_', '-')}", value])
    return subprocess.run(
        command,
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=5,
    )


def seed_topic(workspace: Path, **arguments) -> Path:
    invoke_memory_write(workspace, **arguments)
    return Path()


class TestArchiveTopic:
    def test_moves_topic_file_to_archive_subdirectory(self, isolated_environment):
        fake_home, workspace = isolated_environment
        invoke_memory_write(
            workspace,
            type="user",
            key="lucas",
            fact="lucas prefers pnpm over npm",
            author="lucas",
        )
        result = invoke_memory_prune(workspace, type="user", key="lucas")
        assert result.returncode == 0, result.stderr
        memory_dir = expected_memory_directory(fake_home, workspace)
        assert not (memory_dir / "user-lucas.md").exists()
        assert (memory_dir / "archive" / "user-lucas.md").exists()

    def test_removes_pointer_from_active_memory_index(self, isolated_environment):
        fake_home, workspace = isolated_environment
        invoke_memory_write(
            workspace,
            type="user",
            key="lucas",
            fact="a sufficiently long fact about lucas",
            author="lucas",
        )
        invoke_memory_prune(workspace, type="user", key="lucas")
        memory_dir = expected_memory_directory(fake_home, workspace)
        index_text = (memory_dir / "MEMORY.md").read_text()
        assert "user-lucas.md" not in index_text

    def test_creates_archive_index_with_dated_entry(self, isolated_environment):
        fake_home, workspace = isolated_environment
        invoke_memory_write(
            workspace,
            type="user",
            key="lucas",
            fact="a sufficiently long fact about lucas",
            author="lucas",
        )
        invoke_memory_prune(workspace, type="user", key="lucas")
        memory_dir = expected_memory_directory(fake_home, workspace)
        archive_index = (memory_dir / "archive" / "MEMORY.md").read_text()
        assert "[user/lucas](user-lucas.md)" in archive_index
        assert "archived" in archive_index

    def test_preserves_other_active_memories(self, isolated_environment):
        fake_home, workspace = isolated_environment
        invoke_memory_write(
            workspace,
            type="user",
            key="lucas",
            fact="lucas uses fish shell on macbook",
            author="lucas",
        )
        invoke_memory_write(
            workspace,
            type="feedback",
            key="never-mock-database",
            fact="integration tests must hit real database",
            author="lucas",
        )
        invoke_memory_prune(workspace, type="user", key="lucas")
        memory_dir = expected_memory_directory(fake_home, workspace)
        assert (memory_dir / "feedback-never-mock-database.md").exists()
        index_text = (memory_dir / "MEMORY.md").read_text()
        assert "[feedback/never-mock-database]" in index_text


class TestMissingTopic:
    def test_exits_non_zero_when_topic_does_not_exist(self, isolated_environment):
        _, workspace = isolated_environment
        result = invoke_memory_prune(workspace, type="user", key="never-written")
        assert result.returncode == 1
        assert "not found" in result.stderr.lower()


class TestValidation:
    def test_rejects_invalid_type(self, isolated_environment):
        _, workspace = isolated_environment
        result = invoke_memory_prune(workspace, type="garbage", key="x")
        assert result.returncode == 2
        assert "type" in result.stderr.lower()

    def test_rejects_empty_key(self, isolated_environment):
        _, workspace = isolated_environment
        result = invoke_memory_prune(workspace, type="user", key="")
        assert result.returncode == 2


# --------------------------------------------------------------------------- #
# Pure-function unit tests.                                                   #
# --------------------------------------------------------------------------- #


class TestSlugifyKey:
    def test_matches_memory_write_slugging(self):
        assert memory_prune.slugify_key("Lucas Zanoni") == "lucas-zanoni"
        assert memory_prune.slugify_key("--abc--") == "abc"
        assert memory_prune.slugify_key("UserName") == "username"


class TestTopicFilenameFor:
    def test_combines_type_and_slugged_key(self):
        assert memory_prune.topic_filename_for("user", "Lucas") == "user-lucas.md"
