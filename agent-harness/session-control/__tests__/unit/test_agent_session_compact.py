import time

from agent_session_command_runner import (
    TURN_END_WAIT_CALL,
    deferred_herdr_calls,
    run_command,
)


def test_compact_submits_the_command_only_after_the_turn_ends(tmp_path):
    result = run_command(tmp_path, ["compact"])

    assert result.returncode == 0
    assert "queued" in result.stdout
    assert deferred_herdr_calls(tmp_path, 2) == [
        TURN_END_WAIT_CALL,
        "agent prompt w1:p2 /compact",
    ]


def test_compact_submits_nothing_when_the_turn_end_wait_fails(tmp_path):
    result = run_command(tmp_path, ["compact"], {"HERDR_WAIT_EXIT_STATUS": "1"})

    assert result.returncode == 0
    assert deferred_herdr_calls(tmp_path, 1) == [TURN_END_WAIT_CALL]
    time.sleep(0.5)
    assert deferred_herdr_calls(tmp_path, 1) == [TURN_END_WAIT_CALL]


def test_compact_stays_available_to_clawde_owned_sessions(tmp_path):
    result = run_command(tmp_path, ["compact"], {"CLAWDE_AGENT_NAME": "steward"})

    assert result.returncode == 0
    assert deferred_herdr_calls(tmp_path, 2)[-1] == "agent prompt w1:p2 /compact"
