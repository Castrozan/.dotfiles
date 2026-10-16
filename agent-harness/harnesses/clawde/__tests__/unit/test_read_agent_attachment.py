from pathlib import Path

import pytest

import read_agent_attachment as reader


@pytest.fixture
def attachment(tmp_path, monkeypatch, media_agent_workspace):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    inbox = tmp_path / ".claude/channels/discord/monster/inbox/123"
    inbox.mkdir(parents=True)
    attachment = inbox / "0-message.txt"
    attachment.write_text("X-Men (1992) — T1 a T5", encoding="utf-8")
    return attachment, media_agent_workspace


def test_reads_watchlist_without_modifying_it(attachment):
    path, workspace = attachment
    assert reader.read_attachment(path, workspace) == "X-Men (1992) — T1 a T5"
    assert path.read_text() == "X-Men (1992) — T1 a T5"


@pytest.mark.parametrize(
    "kind", ["outside", "symlink", "oversized", "binary", "directory", "missing"]
)
def test_refuses_paths_and_content_outside_attachment_contract(
    attachment, tmp_path, kind
):
    path, workspace = attachment
    outside = tmp_path / "private.txt"
    outside.write_text("private")
    if kind == "outside":
        path = outside
    elif kind == "symlink":
        path.unlink()
        path.symlink_to(outside)
    elif kind == "oversized":
        path.write_bytes(b"x" * (reader.ATTACHMENT_TEXT_LIMIT_BYTES + 1))
    elif kind == "binary":
        path.write_bytes(b"\x00\xff")
    elif kind == "directory":
        path = path.parent
    else:
        path.unlink()
    with pytest.raises((ValueError, OSError)):
        reader.read_attachment(path, workspace)


def test_refuses_another_agents_inbox(attachment, tmp_path):
    path, workspace = attachment
    other = workspace.parent / "other"
    other.mkdir()
    with pytest.raises(ValueError):
        reader.read_attachment(path, other)
