import sqlite3
from unittest.mock import Mock

import pytest

import shorts_production
import shorts_runner
from shorts_store import TopicStore, write_document


def proposal(key="tardigrade-vacuum"):
    return {
        "topic_key": key,
        "title": key,
        "summary": "How a tiny animal survives vacuum without breathing.",
    }


def configuration():
    return {
        "timezone": "America/Sao_Paulo",
        "hours": [9, 15, 21],
        "model": "gpt-6.1-sol",
        "channel_id": "authorized-channel",
        "browser_profile": "shorts",
        "browser_profile_id": "authorized-profile",
    }


def test_previous_topics_cannot_be_reserved(tmp_path):
    store = TopicStore(tmp_path)
    document = proposal("military-bat-bombs")
    with pytest.raises(ValueError, match="already used"):
        store.reserve(document, "slot")


def test_topic_reservations_are_unique_across_connections(tmp_path):
    first, second = TopicStore(tmp_path), TopicStore(tmp_path)
    first.reserve(proposal(), "morning")
    document = proposal()
    with pytest.raises(ValueError, match="already used"):
        second.reserve(document, "afternoon")


def test_one_run_cannot_reserve_multiple_topics(tmp_path):
    store = TopicStore(tmp_path)
    store.reserve(proposal(), "morning")
    document = proposal("venus-day-length")
    with pytest.raises(sqlite3.IntegrityError):
        store.reserve(document, "morning")


def test_unowned_topic_cannot_be_dispatched(tmp_path, monkeypatch):
    directory = tmp_path / "runs" / "slot"
    directory.mkdir(parents=True)
    monkeypatch.chdir(directory)
    write_document(directory / "episode.json", proposal())
    with pytest.raises(ValueError, match="own the reserved"):
        shorts_production.episode_command(
            "dispatch", tmp_path, directory / "episode.json"
        )
    assert not (directory / "publication.json").exists()


def verified_run(tmp_path, monkeypatch):
    directory = tmp_path / "runs" / "slot"
    directory.mkdir(parents=True)
    monkeypatch.chdir(directory)
    document = {**proposal(), "video": "short.mp4"}
    TopicStore(tmp_path).reserve(document, "slot")
    video = directory / "short.mp4"
    video.write_bytes(b"verified")
    write_document(
        directory / "verification.json", {"sha256": shorts_production.digest(video)}
    )
    write_document(directory / "episode.json", document)
    return directory


def test_changed_video_cannot_be_dispatched(tmp_path, monkeypatch):
    directory = verified_run(tmp_path, monkeypatch)
    (directory / "short.mp4").write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed after verification"):
        shorts_production.episode_command(
            "dispatch", tmp_path, directory / "episode.json"
        )


def test_dispatch_cannot_be_repeated(tmp_path, monkeypatch):
    directory = verified_run(tmp_path, monkeypatch)
    assert (
        shorts_production.episode_command(
            "dispatch", tmp_path, directory / "episode.json"
        )["status"]
        == "dispatch_recorded"
    )
    with pytest.raises(ValueError, match="already dispatched"):
        shorts_production.episode_command(
            "dispatch", tmp_path, directory / "episode.json"
        )


def agent_launcher(tmp_path, monkeypatch, returncode):
    write_document(
        tmp_path / "publisher-ready.json",
        {
            "status": "ready",
            "channel_id": "authorized-channel",
            "browser_profile": "shorts",
            "browser_profile_id": "authorized-profile",
        },
    )
    prompt = tmp_path / "goal.txt"
    prompt.write_text("Produce exactly one video")
    monkeypatch.setenv("SHORTS_CODEX", "/bin/codex")
    monkeypatch.setenv("SHORTS_GOAL_PROMPT", str(prompt))
    process = Mock()
    process.wait.return_value = returncode
    start = Mock(return_value=process)
    monkeypatch.setattr(shorts_runner.subprocess, "Popen", start)
    monkeypatch.setattr(shorts_runner, "browser_instance", lambda configuration: {})
    return start


@pytest.mark.parametrize("channel", [None, "another-channel"])
def test_unverified_publisher_cannot_launch_or_claim_slot(
    tmp_path, monkeypatch, channel
):
    start = Mock()
    monkeypatch.setattr(shorts_runner.subprocess, "Popen", start)
    if channel:
        write_document(
            tmp_path / "publisher-ready.json",
            {"status": "ready", "channel_id": channel, "browser_profile": "shorts"},
        )
    result = shorts_runner.start_run(tmp_path, 9, configuration())
    assert result["status"] == "skipped"
    assert "Publisher" in result["reason"]
    assert not (tmp_path / "runs").exists()
    start.assert_not_called()


def test_same_slot_launches_only_one_fresh_agent(tmp_path, monkeypatch):
    start = agent_launcher(tmp_path, monkeypatch, 0)
    assert (
        shorts_runner.start_run(tmp_path, 9, configuration())["status"]
        == "agent_finished"
    )
    assert shorts_runner.start_run(tmp_path, 9, configuration())["status"] == "skipped"
    assert start.call_count == 1
    arguments = start.call_args.args[0]
    assert "resume" not in arguments
    assert arguments[-2:] == ["--", "Produce exactly one video"]
    assert "gpt-6.1-sol" in arguments
    assert "mcp_servers.chrome-devtools.enabled=false" not in arguments
    assert start.call_args.kwargs["env"]["CLAWDE_AGENT_NAME"] == "shorts-production"


def test_failed_agent_leaves_claimed_slot_for_inspection(tmp_path, monkeypatch):
    agent_launcher(tmp_path, monkeypatch, 1)
    assert (
        shorts_runner.start_run(tmp_path, 15, configuration())["status"]
        == "needs_inspection"
    )
    assert shorts_runner.start_run(tmp_path, 15, configuration())["status"] == "skipped"


def test_unavailable_browser_does_not_spend_a_production_session(tmp_path, monkeypatch):
    start = agent_launcher(tmp_path, monkeypatch, 0)
    monkeypatch.setattr(
        shorts_runner,
        "browser_instance",
        Mock(side_effect=ValueError("Shorts browser unavailable")),
    )
    result = shorts_runner.start_run(tmp_path, 15, configuration())
    assert result == {"status": "skipped", "reason": "Shorts browser unavailable"}
    start.assert_not_called()
    assert not (tmp_path / "runs").exists()


def test_episode_document_must_be_inside_its_run(tmp_path, monkeypatch):
    directory = tmp_path / "runs" / "slot"
    directory.mkdir(parents=True)
    monkeypatch.chdir(directory)
    outside = tmp_path / "outside.json"
    write_document(outside, proposal())
    with pytest.raises(ValueError, match="Evidence must exist inside"):
        shorts_production.episode_command("reserve", tmp_path, outside)
    assert not (tmp_path / "topics.sqlite").exists()
