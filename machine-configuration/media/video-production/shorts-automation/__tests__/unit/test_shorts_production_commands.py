import json
import os
from pathlib import Path
from unittest.mock import Mock

import pytest

import shorts_composition
import shorts_production
import shorts_recovery
import shorts_runner
from shorts_store import TopicStore, write_document

RUN_CONFIGURATION = {"timezone": "America/Sao_Paulo", "hours": [9, 15, 21]}
RESERVED_TOPIC = {
    "topic_key": "tardigrade-vacuum",
    "title": "tardigrade-vacuum",
    "summary": "How a tiny animal survives vacuum without breathing.",
}


def parsed(*command):
    return shorts_production.build_parser().parse_args(list(command))


@pytest.fixture
def configured_state(tmp_path, monkeypatch):
    write_document(tmp_path / "configuration.json", RUN_CONFIGURATION)
    monkeypatch.setenv("SHORTS_CONFIGURATION", str(tmp_path / "configuration.json"))
    return tmp_path


def test_run_action_starts_the_requested_slot(configured_state, monkeypatch):
    start = Mock(return_value={"status": "agent_finished"})
    monkeypatch.setattr(shorts_runner, "start_run", start)
    result = shorts_production.execute_action(
        parsed("run", "--slot", "15"), configured_state
    )
    assert result == {"status": "agent_finished"}
    start.assert_called_once_with(configured_state, 15, RUN_CONFIGURATION)


def test_history_action_lists_reserved_topics(tmp_path):
    TopicStore(tmp_path).reserve(RESERVED_TOPIC, "morning")
    result = shorts_production.execute_action(parsed("history"), tmp_path)
    assert RESERVED_TOPIC["topic_key"] in [row["topic_key"] for row in result]


def test_build_action_composes_inside_the_current_run(tmp_path, monkeypatch):
    directory = tmp_path / "runs" / "slot"
    directory.mkdir(parents=True)
    monkeypatch.chdir(directory)
    build = Mock(return_value={"status": "built"})
    monkeypatch.setattr(shorts_composition, "build_composition", build)
    result = shorts_production.execute_action(
        parsed("build", "--manifest", "manifest.json"), tmp_path
    )
    assert result == {"status": "built"}
    build.assert_called_once_with(directory.resolve(), tmp_path, Path("manifest.json"))


@pytest.mark.parametrize(
    "command",
    [
        ("queue-recovery", "--run-id", "2026-10-31-0900"),
        ("recover-next",),
        ("drain-recovery",),
    ],
)
def test_recovery_actions_reach_the_recovery_command(
    configured_state, monkeypatch, command
):
    recover = Mock(return_value={"status": "recovered"})
    monkeypatch.setattr(shorts_recovery, "command", recover)
    arguments = parsed(*command)
    result = shorts_production.execute_action(arguments, configured_state)
    assert result == {"status": "recovered"}
    recover.assert_called_once_with(arguments, configured_state, RUN_CONFIGURATION)


@pytest.mark.parametrize("action", ["reserve", "verify", "dispatch", "complete"])
def test_episode_actions_reach_the_episode_command(tmp_path, monkeypatch, action):
    episode = Mock(return_value={"status": action})
    monkeypatch.setattr(shorts_production, "episode_command", episode)
    result = shorts_production.execute_action(
        parsed(action, "--episode-file", "episode.json"), tmp_path
    )
    assert result == {"status": action}
    episode.assert_called_once_with(action, tmp_path, Path("episode.json"))


def test_unknown_action_is_rejected_by_the_parser():
    with pytest.raises(SystemExit):
        parsed("publish-everything")


def test_main_prints_the_action_result_and_restricts_new_files(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("SHORTS_STATE_DIRECTORY", str(tmp_path))
    monkeypatch.setattr("sys.argv", ["shorts_production", "history"])
    previous_umask = os.umask(0)
    os.umask(previous_umask)
    try:
        shorts_production.main()
        applied_umask = os.umask(previous_umask)
    finally:
        os.umask(previous_umask)
    printed = json.loads(capsys.readouterr().out)
    assert printed == TopicStore(tmp_path).history()
    assert applied_umask == 0o077
