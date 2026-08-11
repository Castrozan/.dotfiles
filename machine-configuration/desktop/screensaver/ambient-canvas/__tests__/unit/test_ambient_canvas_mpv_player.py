import os

import ambient_canvas_shuffled_segment_order as shuffle_order
from ambient_canvas_playback_dwell_override import effective_dwell_seconds
from mpv_ambient_canvas_player import (
    build_mpv_arguments,
    resolve_segment_dwell,
)
from play_ambient_canvas_loop_mpv import parse_player_arguments, set_process_name


class DeterministicRandomSource:
    def __init__(self, values):
        self.values = list(values)
        self.calls = 0

    def shuffle(self, items):
        self.calls += 1
        items[:] = list(self.values)


def test_shuffled_segment_order_visits_every_segment_before_repeating():
    segment_order = shuffle_order.ShuffledSegmentOrder(
        3, DeterministicRandomSource([2, 0, 1])
    )
    visited = [segment_order.next_segment_index() for _ in range(3)]
    assert sorted(visited) == [0, 1, 2]


def test_shuffled_segment_order_refills_after_one_cycle():
    segment_order = shuffle_order.ShuffledSegmentOrder(
        2, DeterministicRandomSource([1, 0])
    )
    assert segment_order.next_segment_index() == 1
    assert segment_order.next_segment_index() == 0
    assert segment_order.next_segment_index() == 1


def test_shuffled_segment_order_never_repeats_across_the_seam():
    order_one = shuffle_order.ShuffledSegmentOrder(
        3, DeterministicRandomSource([2, 0, 1])
    )
    assert order_one.next_segment_index() == 2
    assert order_one.next_segment_index() == 0
    refilled = shuffle_order.ShuffledSegmentOrder(
        3, DeterministicRandomSource([2, 0, 1])
    )
    assert refilled.next_segment_index() == 2


def test_dwell_override_reads_the_requested_value_from_the_file(tmp_path):
    override_path = tmp_path / "dwell"
    override_path.write_text("12")
    assert effective_dwell_seconds(30, str(override_path)) == 12


def test_dwell_override_clamps_to_the_recorded_dwell():
    override_path = "/nonexistent/dwell"
    assert effective_dwell_seconds(30, override_path) == 30


def test_dwell_override_never_below_the_shortest_allowed_dwell(tmp_path):
    override_path = tmp_path / "dwell"
    override_path.write_text("0.5")
    assert effective_dwell_seconds(30, str(override_path)) == 2.0


def test_dwell_override_ignores_a_missing_or_garbage_file(tmp_path):
    garbage_path = tmp_path / "garbage"
    garbage_path.write_text("not a number")
    assert effective_dwell_seconds(30, str(garbage_path)) == 30


def test_mpv_arguments_pin_the_window_title_and_screensaver_flags():
    arguments = build_mpv_arguments("/tmp/ambient-canvas.sock")
    assert "--force-window=yes" in arguments
    assert "--title=ambient-canvas-gpu-screensaver" in arguments
    assert "--audio=no" in arguments
    assert "--input-ipc-server=/tmp/ambient-canvas.sock" in arguments


def test_process_name_is_set_to_the_pinned_player_marker():
    set_process_name("ᓚᘏᗢ")
    with open(f"/proc/{os.getpid()}/comm") as comm_file:
        assert comm_file.read().strip() == "ᓚᘏᗢ"


def test_parse_player_arguments_reads_manifest_then_dwell_override():
    manifest_path, dwell_override_path = parse_player_arguments(
        ["/state/loops/1660x1080/loop.segments.json", "/state/playback-dwell-seconds"]
    )
    assert manifest_path == "/state/loops/1660x1080/loop.segments.json"
    assert dwell_override_path == "/state/playback-dwell-seconds"


def test_resolve_segment_dwell_applies_the_override_file(tmp_path):
    override_path = tmp_path / "dwell"
    override_path.write_text("15")
    dwell = resolve_segment_dwell({"durationSeconds": 30}, str(override_path))
    assert dwell == 15
