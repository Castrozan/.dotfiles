import pathlib

import ambient_canvas_shuffled_segment_order as shuffle_order

AMBIENT_CANVAS_DIRECTORY = pathlib.Path(__file__).resolve().parents[2]
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


class DeterministicRandomSource:
    def shuffle(self, items):
        items.sort()


def test_video_sequence_advances_without_changing_random_scene_frequency():
    segment_order = shuffle_order.ShuffledSegmentOrder(
        ["take-on-me", None, "take-on-me"], DeterministicRandomSource()
    )
    assert [segment_order.next_segment_index() for _ in range(4)] == [0, 1, 2, 1]


def test_darwin_player_groups_chunks_by_the_same_manifest_sequence():
    assert "let sequence: String?" in SWIFT_MANIFEST_SOURCE
    assert "sequenceIdentifiers: segments.map(\\.sequence)" in SWIFT_PLAYBACK_SOURCE
