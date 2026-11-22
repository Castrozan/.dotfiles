from datetime import UTC
from pathlib import Path

import pytest
import switch_records
import switch_report
import transcript_log
from hypothesis import given, strategies
from switch_log_fakes import (
    CONVERSATION,
    FULL_CHAIN_OFFSETS,
    HEARD_AT,
    OTHER_PANE,
    TARGET,
    RecordingClock,
    at,
    heard_entry,
    replied_after_an_interrupted_attempt,
    switched_to_the_target,
)
from switch_moments import BOUNDARIES, switches_in

RECORDED = Path(__file__).with_name("recorded-wake.log")


def switches_from(lines):
    return switches_in(switch_records.logged_records(lines))


def offsets(switch):
    return {
        name: None if moment is None else moment - HEARD_AT
        for name, moment in switch.moments.items()
    }


def summary_row(text, stage):
    return next(
        line
        for line in text.splitlines()
        if line == f"  {stage}" or (line.startswith(f"  {stage}  "))
    ).split()


def test_todays_recorded_switches_time_the_routing_decision():
    tamamo, anastasia = switches_from(RECORDED.read_text().splitlines())
    assert (tamamo.servant, tamamo.sequence, tamamo.delivered) == ("Tamamo", 75, None)
    assert (anastasia.servant, anastasia.sequence) == ("Anastasia", 80)
    decision = [
        switch_report.took(switch.moments, "decision_started", "decision_done")
        for switch in (tamamo, anastasia)
    ]
    assert decision == pytest.approx([0.628, 0.380], abs=1e-6)
    assembly = switch_report.took(tamamo.moments, "wake_read", "decision_started")
    assert assembly == pytest.approx(0.036468, abs=1e-6)
    unrecorded = {name for name, moment in tamamo.moments.items() if moment is None}
    assert unrecorded == set(BOUNDARIES) - {
        "wake_read",
        "decision_started",
        "decision_done",
    }
    report = switch_report.report([tamamo, anastasia], UTC)
    assert summary_row(report, "decision API")[2:] == ["2", "0.380", "s", "0.628", "s"]
    assert summary_row(report, "end to end")[3:] == ["0", "-", "-"]


def test_every_boundary_of_a_switch_is_read_from_the_recorded_log(monkeypatch):
    clock = RecordingClock(monkeypatch)
    switched_to_the_target(clock)
    replied_after_an_interrupted_attempt(clock)
    (switch,) = switches_from(clock.lines)
    assert offsets(switch) == pytest.approx(FULL_CHAIN_OFFSETS, abs=1e-3)
    assert (switch.servant, switch.pane, switch.delivered) == (
        "Ibaraki-dōji",
        TARGET,
        "prompt",
    )
    assert switch.switched_at == pytest.approx(at(2.4), abs=1e-6)
    report = switch_report.report([switch], UTC)
    assert "  end to end 10.650 s" in report
    assert summary_row(report, "agent wake-up")[2:] == ["1", "3.450", "s", "3.450", "s"]


def test_the_next_switch_ends_what_the_previous_agent_can_claim(monkeypatch):
    clock = RecordingClock(monkeypatch)
    switched_to_the_target(clock)
    clock.record(4.0, transcript_log.report_conversation, heard_entry(81, "voltei"))
    clock.record(
        5.0,
        transcript_log.report_delivery,
        purpose=CONVERSATION,
        sequence=81,
        servant="Voyager",
        pane=OTHER_PANE,
        host=None,
        delivered="notify",
        delivery_ms=40,
    )
    replied_after_an_interrupted_attempt(clock)
    first, greeted = switches_from(clock.lines)
    assert first.moments["agent_first_command"] is None
    assert first.moments["first_audio"] is None
    assert greeted.moments["decision_done"] is None
    assert greeted.switched_at == pytest.approx(at(5.0), abs=1e-6)
    recorded = {name for name, moment in offsets(greeted).items() if moment is not None}
    assert recorded == {
        "speech_ended",
        "segment_closed",
        "transcription_started",
        "transcript_written",
        "wake_read",
        "prompt_sent",
        "prompt_delivered",
    }, "the other pane spoke only before its own switch"


def test_only_a_switch_inside_a_conversation_is_measured(monkeypatch):
    clock = RecordingClock(monkeypatch)
    for purpose in (None, "meeting"):
        clock.record(
            1.0,
            transcript_log.report_delivery,
            purpose=purpose,
            sequence=None,
            servant="Voyager",
            pane=OTHER_PANE,
            host=None,
            delivered="prompt",
            delivery_ms=10,
        )
    clock.record(
        2.0,
        transcript_log.report_addressing,
        CONVERSATION,
        sequence=9,
        candidates=["Voyager"],
        latency_ms=300,
        verdict="keep",
        choice="holder",
        confidence=0.9,
    )
    assert switches_from([*clock.lines, "{broken", "wake Voyager at w0:p7"]) == []


@given(
    strategies.lists(strategies.floats(0, 60), min_size=1, max_size=40),
    strategies.integers(1, 100),
)
def test_a_nearest_rank_percentile_splits_the_measurements_at_its_rank(
    values, percentile
):
    rank = switch_report.nearest_rank(values, percentile)
    assert rank in values
    assert sum(value <= rank for value in values) >= percentile / 100 * len(values)
    assert sum(value < rank for value in values) < percentile / 100 * len(values)
