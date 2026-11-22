import dataclasses
import shutil
import stat
import sys
from pathlib import Path

import switch_latency
import transcript_log
from switch_moments import Switch

RECORDED = Path(__file__).with_name("recorded-wake.log")


def wake_log_in(state, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(state))
    wake_log = transcript_log.wake_log_path()
    wake_log.parent.mkdir(parents=True)
    shutil.copy(RECORDED, wake_log)
    return wake_log


def switch_at(switched_at, servant="Voyager"):
    return Switch(switched_at, servant, None, 1, None, {})


def test_switches_outlive_the_rotation_of_the_wake_log(tmp_path, monkeypatch):
    wake_log = wake_log_in(tmp_path, monkeypatch)
    measured = switch_latency.recorded_switches(wake_log)
    wake_log.write_text("")
    assert switch_latency.recorded_switches(wake_log) == measured
    history = wake_log.with_name(switch_latency.HISTORY_FILE)
    assert [switch.sequence for switch in measured] == [75, 80]
    assert stat.S_IMODE(history.stat().st_mode) == 0o600


def test_the_history_keeps_the_newest_switches_and_the_freshest_reading():
    kept = switch_latency.KEPT_SWITCHES
    remembered = [switch_at(float(moment)) for moment in range(kept + 5)]
    fresh = [switch_at(float(kept + 4), servant="Ibaraki")]
    merged = switch_latency.merged(remembered, fresh)
    assert len(merged) == kept
    assert merged[0].switched_at == 5.0
    assert merged[-1].servant == "Ibaraki"


def test_a_kept_switch_reads_back_unchanged(tmp_path):
    switch = dataclasses.replace(
        switch_at(1_795_382_485.0), moments={"wake_read": 1_795_382_486.25}
    )
    history = tmp_path / "avatar" / switch_latency.HISTORY_FILE
    switch_latency.keep(history, [switch])
    assert switch_latency.remembered(history) == [switch]


def test_the_command_reports_only_the_switches_inside_its_window(
    tmp_path, monkeypatch, capsys
):
    wake_log_in(tmp_path, monkeypatch)
    window = ["--since", "2026-11-22T21:20:00+00:00", "--until", "2026-11-23"]
    monkeypatch.setattr(sys, "argv", ["avatar-switch-latency", *window])
    switch_latency.main()
    printed = capsys.readouterr().out
    assert "Switch to Anastasia" in printed
    assert "Switch to Tamamo" not in printed
    assert "Across 1 switches" in printed


def test_recording_keeps_the_switches_and_prints_nothing(tmp_path, monkeypatch, capsys):
    wake_log = wake_log_in(tmp_path, monkeypatch)
    monkeypatch.setattr(sys, "argv", ["avatar-switch-latency", "--record"])
    switch_latency.main()
    assert capsys.readouterr().out == ""
    assert (
        len(switch_latency.remembered(wake_log.with_name("switch-latency.jsonl"))) == 2
    )
