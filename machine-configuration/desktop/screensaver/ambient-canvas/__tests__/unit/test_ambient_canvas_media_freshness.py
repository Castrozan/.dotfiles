import json

import ensure_ambient_canvas_screensaver as ensure


def _write_recorded_loop(output_directory, source_identifier):
    _write_segment_manifest(output_directory)
    (output_directory / "segments").mkdir(exist_ok=True)
    (output_directory / "segments" / "abc123.mp4").write_bytes(b"media")
    (output_directory / "loop.source").write_text(source_identifier + "\n")


def _write_segment_manifest(output_directory):
    (output_directory / "loop.segments.json").write_text(
        json.dumps(
            {"segments": [{"file": "segments/abc123.mp4", "durationSeconds": 30}]}
        )
    )


def test_recorded_loop_is_fresh_true_when_source_matches(tmp_path):
    _write_recorded_loop(tmp_path, "/store/web-abc")
    assert ensure.recorded_loop_is_fresh(str(tmp_path), "/store/web-abc") is True


def test_recorded_loop_is_fresh_false_on_source_mismatch(tmp_path):
    _write_recorded_loop(tmp_path, "/store/web-old")
    assert ensure.recorded_loop_is_fresh(str(tmp_path), "/store/web-new") is False


def test_recorded_loop_is_fresh_false_when_a_segment_is_missing(tmp_path):
    _write_segment_manifest(tmp_path)
    (tmp_path / "loop.source").write_text("/store/web-abc\n")
    assert ensure.recorded_loop_is_fresh(str(tmp_path), "/store/web-abc") is False


def test_recorded_loop_is_fresh_false_when_nothing_rendered(tmp_path):
    assert ensure.recorded_loop_is_fresh(str(tmp_path), "/store/web-abc") is False


def test_recorded_loop_exists_true_when_every_segment_is_present(tmp_path):
    _write_recorded_loop(tmp_path, "/store/web-abc")
    assert ensure.recorded_loop_exists(str(tmp_path)) is True


def test_a_rebuilt_web_source_makes_the_recorded_loop_stale(tmp_path):
    previous_build = ensure.compose_recorded_source_identifier(
        "/store/web-abc", "1660x1080"
    )
    _write_recorded_loop(tmp_path, previous_build)
    assert ensure.recorded_loop_is_fresh(str(tmp_path), previous_build) is True
    assert (
        ensure.recorded_loop_is_fresh(
            str(tmp_path),
            ensure.compose_recorded_source_identifier("/store/web-new", "1660x1080"),
        )
        is False
    )


def test_recorded_loop_exists_false_when_absent(tmp_path):
    assert ensure.recorded_loop_exists(str(tmp_path)) is False
