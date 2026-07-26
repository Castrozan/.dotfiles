import json
import os

import recorded_segment_store as store

SWIFT_MANIFEST_SOURCE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "swift-sources",
    "ambient-canvas-recorded-segment-manifest.swift",
)
WEB_RECORDER_SOURCE = os.path.join(
    os.path.dirname(__file__), "..", "..", "web", "recorder.js"
)


def read_source(source_path):
    with open(source_path) as source_file:
        return source_file.read()


def build_uploaded_manifest_bytes(*fingerprints):
    return json.dumps(
        {
            "segments": [
                {
                    "fingerprint": fingerprint,
                    "extension": "mp4",
                    "durationSeconds": 30,
                }
                for fingerprint in fingerprints
            ]
        }
    ).encode()


def test_stored_segment_lands_under_its_fingerprint(tmp_path):
    stored_path = store.store_recorded_segment(str(tmp_path), "abc123", "mp4", b"media")
    assert stored_path == str(tmp_path / "segments" / "abc123.mp4")
    assert (tmp_path / "segments" / "abc123.mp4").read_bytes() == b"media"


def test_stored_segments_are_listed_by_fingerprint(tmp_path):
    store.store_recorded_segment(str(tmp_path), "abc123", "mp4", b"media")
    store.store_recorded_segment(str(tmp_path), "def456", "mp4", b"media")
    assert store.list_recorded_segment_fingerprints(str(tmp_path)) == [
        "abc123",
        "def456",
    ]


def test_no_segments_are_listed_before_the_first_recording(tmp_path):
    assert store.list_recorded_segment_fingerprints(str(tmp_path)) == []


def test_an_interrupted_upload_is_not_listed_as_recorded(tmp_path):
    store.store_recorded_segment(str(tmp_path), "abc123", "mp4", b"media")
    (tmp_path / "segments" / "tmp9999.staging").write_bytes(b"partial")
    assert store.list_recorded_segment_fingerprints(str(tmp_path)) == ["abc123"]


def test_uploaded_manifest_becomes_segment_file_paths():
    uploaded_segments = store.parse_uploaded_segment_manifest(
        build_uploaded_manifest_bytes("abc123")
    )
    assert store.build_recorded_segment_manifest(uploaded_segments) == {
        "segments": [{"file": "segments/abc123.mp4", "durationSeconds": 30}]
    }


def test_uploaded_manifest_without_fingerprints_is_rejected():
    assert (
        store.parse_uploaded_segment_manifest(
            json.dumps({"segments": [{"durationSeconds": 30}]}).encode()
        )
        is None
    )


def test_empty_uploaded_manifest_is_rejected():
    assert store.parse_uploaded_segment_manifest(b'{"segments": []}') is None


def test_unparseable_uploaded_manifest_is_rejected():
    assert store.parse_uploaded_segment_manifest(b"not json") is None


def test_manifest_is_playable_once_every_segment_is_stored(tmp_path):
    store.store_recorded_segment(str(tmp_path), "abc123", "mp4", b"media")
    store.write_recorded_segment_manifest(
        str(tmp_path),
        store.build_recorded_segment_manifest(
            store.parse_uploaded_segment_manifest(
                build_uploaded_manifest_bytes("abc123")
            )
        ),
    )
    assert store.resolve_playable_segment_manifest_path(str(tmp_path)) == str(
        tmp_path / "loop.segments.json"
    )


def test_manifest_referencing_a_missing_segment_is_not_playable(tmp_path):
    store.write_recorded_segment_manifest(
        str(tmp_path),
        store.build_recorded_segment_manifest(
            store.parse_uploaded_segment_manifest(
                build_uploaded_manifest_bytes("abc123")
            )
        ),
    )
    assert store.resolve_playable_segment_manifest_path(str(tmp_path)) is None


def test_manifest_is_not_playable_before_the_first_recording(tmp_path):
    assert store.resolve_playable_segment_manifest_path(str(tmp_path)) is None


def test_pruning_keeps_the_segments_the_manifest_references(tmp_path):
    store.store_recorded_segment(str(tmp_path), "kept", "mp4", b"media")
    store.store_recorded_segment(str(tmp_path), "dropped", "mp4", b"media")
    recorded_manifest = store.build_recorded_segment_manifest(
        store.parse_uploaded_segment_manifest(build_uploaded_manifest_bytes("kept"))
    )
    pruned = store.prune_recorded_segments_outside_manifest(
        str(tmp_path), recorded_manifest
    )
    assert pruned == [str(tmp_path / "segments" / "dropped.mp4")]
    assert store.list_recorded_segment_fingerprints(str(tmp_path)) == ["kept"]


def test_a_segment_reused_twice_survives_pruning(tmp_path):
    store.store_recorded_segment(str(tmp_path), "twice", "mp4", b"media")
    recorded_manifest = store.build_recorded_segment_manifest(
        store.parse_uploaded_segment_manifest(
            build_uploaded_manifest_bytes("twice", "twice")
        )
    )
    store.prune_recorded_segments_outside_manifest(str(tmp_path), recorded_manifest)
    assert store.list_recorded_segment_fingerprints(str(tmp_path)) == ["twice"]


def test_source_identifier_round_trips(tmp_path):
    store.write_recorded_source_identifier(str(tmp_path), "/store/web-abc")
    assert store.read_recorded_source_identifier(str(tmp_path)) == "/store/web-abc"


def test_absent_source_identifier_reads_as_none(tmp_path):
    assert store.read_recorded_source_identifier(str(tmp_path)) is None


def test_swift_reader_and_python_writer_agree_on_the_field_names():
    swift_source = read_source(SWIFT_MANIFEST_SOURCE)
    for field_name in ("file", "durationSeconds", "segments"):
        assert field_name in swift_source


def test_web_recorder_uploads_the_fields_the_store_parses():
    recorder_source = read_source(WEB_RECORDER_SOURCE)
    for field_name in ("fingerprint", "extension", "durationSeconds"):
        assert field_name in recorder_source
