import pathlib

import pytest

import mpv_ambient_canvas_player as mpv_player
import ambient_canvas_shuffled_segment_order as shuffle_order

AMBIENT_CANVAS_DIRECTORY = pathlib.Path(__file__).resolve().parents[3]
SWIFT_MANIFEST_SOURCE = (
    AMBIENT_CANVAS_DIRECTORY
    / "swift-sources"
    / "ambient-canvas-recorded-segment-manifest.swift"
).read_text()
SWIFT_PLAYBACK_SOURCE = (
    AMBIENT_CANVAS_DIRECTORY
    / "swift-sources"
    / "ambient-canvas-shuffled-segment-playback.swift"
).read_text()
PYTHON_PLAYBACK_SOURCE = (
    AMBIENT_CANVAS_DIRECTORY
    / "scripts"
    / "ambient_canvas_media"
    / "mpv_ambient_canvas_player.py"
).read_text()


class DeterministicRandomSource:
    def shuffle(self, items):
        items.sort()


def test_video_sequence_chunks_stay_together_as_one_shuffle_choice():
    segment_order = shuffle_order.ShuffledSegmentOrder(
        ["take-on-me", None, "take-on-me"], DeterministicRandomSource()
    )
    assert [segment_order.next_segment_indices() for _ in range(3)] == [
        [0, 2],
        [1],
        [0, 2],
    ]


def test_linux_player_finishes_each_sequence_before_choosing_another():
    assert "for segment_index in segment_order.next_segment_indices():" in (
        PYTHON_PLAYBACK_SOURCE
    )


def test_linux_player_plays_each_video_sequence_contiguously(monkeypatch):
    class PlaybackFinished(Exception):
        pass

    class MappedMpvClient:
        def __init__(self):
            self.commands = []

        def send_command(self, command):
            self.commands.append(command)

    monkeypatch.setattr(
        mpv_player,
        "ShuffledSegmentOrder",
        lambda sequence_identifiers: shuffle_order.ShuffledSegmentOrder(
            sequence_identifiers, DeterministicRandomSource()
        ),
    )
    completed_segments = 0

    def stop_after_three_segments(_mpv_client):
        nonlocal completed_segments
        completed_segments += 1
        if completed_segments == 3:
            raise PlaybackFinished

    monkeypatch.setattr(mpv_player, "wait_for_end_of_file", stop_after_three_segments)
    mpv_client = MappedMpvClient()

    with pytest.raises(PlaybackFinished):
        mpv_player.play_shuffled_loop(
            mpv_client,
            [
                {"sequence": "evangelion", "durationSeconds": 30},
                {"durationSeconds": 30},
                {"sequence": "evangelion", "durationSeconds": 27.4},
            ],
            ["eva-first.mp4", "other-scene.mp4", "eva-final.mp4"],
            "/nonexistent/dwell",
        )

    loaded_segments = [
        command[1] for command in mpv_client.commands if command[0] == "loadfile"
    ]
    assert loaded_segments == ["eva-first.mp4", "eva-final.mp4", "other-scene.mp4"]


def test_darwin_player_enqueues_sequence_chunks_in_order():
    assert "let sequence: String?" in SWIFT_MANIFEST_SOURCE
    assert "sequenceIdentifiers: segments.map(\\.sequence)" in SWIFT_PLAYBACK_SOURCE
    assert "segmentOrder.nextSegmentIndices()" in SWIFT_PLAYBACK_SOURCE
    assert "pendingSegmentIndices.removeFirst()" in SWIFT_PLAYBACK_SOURCE
