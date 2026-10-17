import json
import subprocess
from unittest.mock import Mock

import pytest

import pipewire_alsa_recovery as recovery


def journal_entry(timestamp, process_id="123", device="front:4p"):
    return json.dumps(
        {
            "MESSAGE": (
                f"spa.alsa: {device}: (62 suppressed) "
                "snd_pcm_avail after recover: Broken pipe"
            ),
            "_PID": process_id,
            "__MONOTONIC_TIMESTAMP": str(int(timestamp * 1_000_000)),
        }
    )


def failure(timestamp, process_id="123", device="front:4p"):
    return recovery.parse_failure(journal_entry(timestamp, process_id, device))


@pytest.mark.parametrize("line", ["", "broken", "[]", "null", "{}", '{"MESSAGE": []}'])
def test_malformed_journal_records_are_ignored(line):
    assert recovery.parse_failure(line) is None


@pytest.mark.parametrize(
    "change",
    [
        {"MESSAGE": "spa.alsa: underrun"},
        {"MESSAGE": "snd_pcm_avail after recover: Broken pipe"},
        {"_PID": None},
        {"_PID": "invalid"},
        {"__MONOTONIC_TIMESTAMP": None},
        {"__MONOTONIC_TIMESTAMP": "invalid"},
    ],
)
def test_only_identified_alsa_recovery_failures_are_accepted(change):
    entry = json.loads(journal_entry(100))
    entry.update(change)
    assert recovery.parse_failure(json.dumps(entry)) is None


def test_persistent_failure_recovers_after_four_seconds():
    policy = recovery.RecoveryPolicy()
    assert not policy.should_recover(failure(100), 100)
    assert not policy.should_recover(failure(102), 102)
    assert policy.should_recover(failure(104), 104)


def test_transient_and_repeated_identical_errors_do_not_restart_audio():
    policy = recovery.RecoveryPolicy()
    for timestamp in [100, 100, 100, 100.1, 100.2, 100.3, 111]:
        assert not policy.should_recover(failure(timestamp), timestamp)


def test_errors_from_distinct_devices_and_processes_are_not_combined():
    policy = recovery.RecoveryPolicy()
    assert not policy.should_recover(failure(100), 100)
    assert not policy.should_recover(failure(102, device="front:5p"), 102)
    assert not policy.should_recover(failure(104, process_id="456"), 104)
    assert not policy.should_recover(failure(106), 106)
    assert policy.should_recover(failure(108), 108)


@pytest.mark.parametrize("timestamp", [89, 101])
def test_old_or_future_journal_entries_do_not_trigger_recovery(timestamp):
    policy = recovery.RecoveryPolicy()
    for _ in range(4):
        assert not policy.should_recover(failure(timestamp), 100)
    assert not policy.failures


def test_recovery_cooldown_requires_fresh_failures_after_one_minute():
    policy = recovery.RecoveryPolicy()
    for timestamp in [100, 102, 104]:
        policy.should_recover(failure(timestamp), timestamp)
    for timestamp in [106, 108, 110, 163]:
        assert not policy.should_recover(failure(timestamp), timestamp)
    assert not policy.should_recover(failure(164), 164)
    assert not policy.should_recover(failure(166), 166)
    assert policy.should_recover(failure(168), 168)


def test_retained_error_history_is_bounded():
    policy = recovery.RecoveryPolicy()
    for process_id in range(1000):
        policy.should_recover(failure(100, str(process_id)), 100)
    assert len(policy.failures) == 32


def test_recovery_restarts_the_verified_audio_services(monkeypatch):
    run = Mock(return_value=subprocess.CompletedProcess([], 0, stdout="123\n"))
    monkeypatch.setattr(recovery.subprocess, "run", run)
    recovery.recover_audio(failure(100))
    assert run.call_args_list[0].args[0][-1] == "pipewire.service"
    assert run.call_args_list[1].args[0] == [
        "systemctl",
        "--user",
        "restart",
        "pipewire.service",
        "pipewire-pulse.service",
        "wireplumber.service",
    ]
    assert run.call_args_list[1].kwargs["timeout"] == 20


def test_queued_errors_cannot_restart_a_new_pipewire_process(monkeypatch):
    run = Mock(return_value=subprocess.CompletedProcess([], 0, stdout="456\n"))
    monkeypatch.setattr(recovery.subprocess, "run", run)
    recovery.recover_audio(failure(100))
    assert run.call_count == 1


def test_recorded_failure_stream_triggers_one_recovery(monkeypatch):
    recover = Mock()
    monkeypatch.setattr(recovery, "recover_audio", recover)
    monkeypatch.setattr(recovery.time, "monotonic", lambda: 106)
    recovery.monitor_failures(
        ["invalid", *(journal_entry(timestamp) for timestamp in [100, 102, 104, 106])]
    )
    recover.assert_called_once_with(failure(104))


@pytest.mark.parametrize(
    "error", [subprocess.TimeoutExpired("systemctl", 20), OSError("unavailable")]
)
def test_failed_recovery_keeps_monitoring_without_a_restart_loop(monkeypatch, error):
    recover = Mock(side_effect=error)
    monkeypatch.setattr(recovery, "recover_audio", recover)
    monkeypatch.setattr(recovery.time, "monotonic", lambda: 108)
    recovery.monitor_failures(
        journal_entry(timestamp) for timestamp in [100, 102, 104, 106, 108]
    )
    assert recover.call_count == 1
