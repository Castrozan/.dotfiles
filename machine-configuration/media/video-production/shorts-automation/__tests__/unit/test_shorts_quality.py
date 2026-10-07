import json
from unittest.mock import Mock

import pytest

import shorts_quality


def test_missing_research_blocks_media_verification(tmp_path):
    with pytest.raises(ValueError, match="Missing research"):
        shorts_quality.verify_episode(tmp_path, {})


def test_evidence_cannot_escape_run_directory(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    (tmp_path / "other.txt").write_text("Other episode")
    with pytest.raises(ValueError, match="inside the current run"):
        shorts_quality.inside_run(run, "../other.txt")


@pytest.mark.parametrize(
    "channel,visibility", [("wrong-channel", "public"), ("expected", "private")]
)
def test_wrong_channel_or_private_video_cannot_complete(
    monkeypatch, channel, visibility
):
    monkeypatch.setattr(
        shorts_quality,
        "command",
        Mock(
            return_value=json.dumps(
                {"channel_id": channel, "availability": visibility, "id": "example"}
            )
        ),
    )
    with pytest.raises(ValueError, match="authorized channel"):
        shorts_quality.verify_publication(
            "https://www.youtube.com/shorts/example", "expected"
        )


def test_publication_url_must_be_youtube(monkeypatch):
    run = Mock()
    monkeypatch.setattr(shorts_quality, "command", run)
    with pytest.raises(ValueError, match="direct YouTube"):
        shorts_quality.verify_publication("https://example.com/video", "expected")
    run.assert_not_called()
