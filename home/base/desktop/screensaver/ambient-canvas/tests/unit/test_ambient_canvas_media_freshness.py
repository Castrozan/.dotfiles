import ensure_ambient_canvas_screensaver as ensure


def _write_recorded_loop(
    output_directory, source_identifier, media_filename="loop.mp4"
):
    (output_directory / media_filename).write_bytes(b"media")
    (output_directory / "loop.current").write_text(media_filename + "\n")
    (output_directory / "loop.source").write_text(source_identifier + "\n")


def test_recorded_loop_is_fresh_true_when_source_matches(tmp_path):
    _write_recorded_loop(tmp_path, "/store/web-abc")
    assert ensure.recorded_loop_is_fresh(str(tmp_path), "/store/web-abc") is True


def test_recorded_loop_is_fresh_false_on_source_mismatch(tmp_path):
    _write_recorded_loop(tmp_path, "/store/web-old")
    assert ensure.recorded_loop_is_fresh(str(tmp_path), "/store/web-new") is False


def test_recorded_loop_is_fresh_false_when_media_missing(tmp_path):
    (tmp_path / "loop.current").write_text("loop.mp4\n")
    (tmp_path / "loop.source").write_text("/store/web-abc\n")
    assert ensure.recorded_loop_is_fresh(str(tmp_path), "/store/web-abc") is False


def test_recorded_loop_is_fresh_false_when_nothing_rendered(tmp_path):
    assert ensure.recorded_loop_is_fresh(str(tmp_path), "/store/web-abc") is False


def test_recorded_loop_exists_true_when_media_present(tmp_path):
    _write_recorded_loop(tmp_path, "/store/web-abc")
    assert ensure.recorded_loop_exists(str(tmp_path)) is True


def test_recorded_loop_exists_false_when_absent(tmp_path):
    assert ensure.recorded_loop_exists(str(tmp_path)) is False
