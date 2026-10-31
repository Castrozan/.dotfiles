import json
import sqlite3
from pathlib import Path
from unittest.mock import Mock

import pytest

import shorts_composition
import shorts_production
import shorts_recovery
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


def test_episode_document_must_be_inside_its_run(tmp_path, monkeypatch):
    directory = tmp_path / "runs" / "slot"
    directory.mkdir(parents=True)
    monkeypatch.chdir(directory)
    outside = tmp_path / "outside.json"
    write_document(outside, proposal())
    with pytest.raises(ValueError, match="Evidence must exist inside"):
        shorts_production.episode_command("reserve", tmp_path, outside)
    assert not (tmp_path / "topics.sqlite").exists()


def configuration_file(tmp_path, monkeypatch):
    path = tmp_path / "configuration.json"
    write_document(path, configuration())
    monkeypatch.setenv("SHORTS_CONFIGURATION", str(path))
    return path


def test_run_action_starts_the_requested_slot(tmp_path, monkeypatch):
    configuration_file(tmp_path, monkeypatch)
    start_run = Mock(return_value={"started": True})
    monkeypatch.setattr(shorts_runner, "start_run", start_run)
    arguments = shorts_production.build_parser().parse_args(["run", "--slot", "15"])
    result = shorts_production.execute_action(arguments, tmp_path)
    assert result == {"started": True}
    start_run.assert_called_once_with(tmp_path, 15, configuration())


def test_history_action_lists_reserved_topics(tmp_path):
    TopicStore(tmp_path).reserve(proposal(), "morning")
    arguments = shorts_production.build_parser().parse_args(["history"])
    result = shorts_production.execute_action(arguments, tmp_path)
    assert "tardigrade-vacuum" in json.dumps(result)


def test_build_action_composes_inside_the_run_directory(tmp_path, monkeypatch):
    directory = tmp_path / "runs" / "slot"
    directory.mkdir(parents=True)
    monkeypatch.chdir(directory)
    build_composition = Mock(return_value={"built": True})
    monkeypatch.setattr(shorts_composition, "build_composition", build_composition)
    arguments = shorts_production.build_parser().parse_args(
        ["build", "--manifest", "manifest.json"]
    )
    result = shorts_production.execute_action(arguments, tmp_path)
    assert result == {"built": True}
    build_composition.assert_called_once_with(
        directory.resolve(), tmp_path, Path("manifest.json")
    )


@pytest.mark.parametrize("action", shorts_recovery.ACTIONS)
def test_recovery_actions_are_handled_by_recovery(action, tmp_path, monkeypatch):
    configuration_file(tmp_path, monkeypatch)
    command = Mock(return_value={"recovered": action})
    monkeypatch.setattr(shorts_recovery, "command", command)
    extra = ["--run-id", "2026-10-31-0900"] if action == "queue-recovery" else []
    arguments = shorts_production.build_parser().parse_args([action, *extra])
    result = shorts_production.execute_action(arguments, tmp_path)
    assert result == {"recovered": action}
    command.assert_called_once_with(arguments, tmp_path, configuration())


@pytest.mark.parametrize("action", ["reserve", "verify", "dispatch", "complete"])
def test_episode_actions_are_handled_by_episode_command(action, tmp_path, monkeypatch):
    episode_command = Mock(return_value={"episode": action})
    monkeypatch.setattr(shorts_production, "episode_command", episode_command)
    arguments = shorts_production.build_parser().parse_args(
        [action, "--episode-file", "episode.json"]
    )
    result = shorts_production.execute_action(arguments, tmp_path)
    assert result == {"episode": action}
    episode_command.assert_called_once_with(action, tmp_path, Path("episode.json"))


def test_unknown_action_is_rejected_by_the_parser():
    with pytest.raises(SystemExit):
        shorts_production.build_parser().parse_args(["publish"])


def test_main_prints_the_action_result_as_json(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SHORTS_STATE_DIRECTORY", str(tmp_path))
    monkeypatch.setattr("sys.argv", ["shorts_production", "history"])
    shorts_production.main()
    assert json.loads(capsys.readouterr().out) == TopicStore(tmp_path).history()
