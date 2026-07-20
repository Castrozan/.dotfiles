import json
import os

from recorded_loop_upload_server import write_recorded_loop_segment_table

SWIFT_SEGMENT_TABLE_SOURCE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "swift-sources",
    "ambient-canvas-recorded-loop-segment-table.swift",
)
WEB_PLAYER_SOURCE = os.path.join(
    os.path.dirname(__file__), "..", "..", "web", "player.js"
)
WEB_ENCODER_SOURCE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "web",
    "record",
    "ambient-canvas-recording-encoder.js",
)


def read_source(source_path):
    with open(source_path) as source_file:
        return source_file.read()


def test_segment_table_is_written_next_to_the_loop(tmp_path):
    write_recorded_loop_segment_table(
        str(tmp_path), json.dumps({"segments": [{"startSeconds": 0}]}).encode()
    )
    written = json.loads((tmp_path / "loop.segments.json").read_text())
    assert written["segments"][0]["startSeconds"] == 0


def test_absent_table_deletes_a_stale_one(tmp_path):
    (tmp_path / "loop.segments.json").write_text('{"segments": []}')
    write_recorded_loop_segment_table(str(tmp_path), None)
    assert not (tmp_path / "loop.segments.json").exists()


def test_empty_table_deletes_a_stale_one(tmp_path):
    (tmp_path / "loop.segments.json").write_text('{"segments": []}')
    write_recorded_loop_segment_table(str(tmp_path), b"")
    assert not (tmp_path / "loop.segments.json").exists()


def test_absent_table_is_a_no_op_when_nothing_exists(tmp_path):
    write_recorded_loop_segment_table(str(tmp_path), None)
    assert not (tmp_path / "loop.segments.json").exists()


def test_swift_reader_and_python_writer_agree_on_the_filename():
    assert "loop.segments.json" in read_source(SWIFT_SEGMENT_TABLE_SOURCE)


def test_swift_reader_and_web_producer_agree_on_the_field_names():
    swift_source = read_source(SWIFT_SEGMENT_TABLE_SOURCE)
    player_source = read_source(WEB_PLAYER_SOURCE)
    for field_name in ("startSeconds", "durationSeconds"):
        assert field_name in swift_source
        assert field_name in player_source
    assert "segments" in swift_source
    assert '"segments"' in read_source(
        WEB_ENCODER_SOURCE
    ) or "segments:" in read_source(WEB_ENCODER_SOURCE)
