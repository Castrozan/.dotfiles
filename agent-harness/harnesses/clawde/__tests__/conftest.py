import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


@pytest.fixture
def media_secrets_directory(tmp_path, monkeypatch):
    secrets_directory = tmp_path / "secrets"
    secrets_directory.mkdir()
    monkeypatch.setenv("CLAWDE_SECRETS_DIRECTORY", str(secrets_directory))
    return secrets_directory


@pytest.fixture
def media_agent_workspace(tmp_path, monkeypatch, media_secrets_directory):
    """An agent workspace with both media keys on hand, as a rebuilt machine has."""
    agents_directory = tmp_path / "clawde"
    workspace = agents_directory / "monster"
    workspace.mkdir(parents=True)
    (media_secrets_directory / "openai-api-key").write_text("sk-test", encoding="utf-8")
    (media_secrets_directory / "gemini-api-key").write_text(
        "gemini-test", encoding="utf-8"
    )
    monkeypatch.setenv("CLAWDE_AGENTS_DIRECTORY", str(agents_directory))
    monkeypatch.delenv("DISCORD_STATE_DIR", raising=False)
    return workspace
