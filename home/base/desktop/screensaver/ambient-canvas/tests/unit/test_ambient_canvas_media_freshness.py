import display_ambient_canvas_loop as display
import ensure_ambient_canvas_screensaver as ensure


def _write_recorded_loop(
    output_directory, source_identifier, media_filename="loop.mp4"
):
    (output_directory / media_filename).write_bytes(b"media")
    (output_directory / "loop.current").write_text(media_filename + "\n")
    (output_directory / "loop.source").write_text(source_identifier + "\n")


def test_resolve_recorded_loop_source_url_is_none_without_pointer(tmp_path):
    assert display.resolve_recorded_loop_source_url(str(tmp_path)) is None


def test_resolve_recorded_loop_source_url_is_none_when_media_missing(tmp_path):
    (tmp_path / "loop.current").write_text("loop.mp4\n")
    assert display.resolve_recorded_loop_source_url(str(tmp_path)) is None


def test_resolve_recorded_loop_source_url_reads_pointer_and_encodes(tmp_path):
    _write_recorded_loop(tmp_path, "/store/web-abc")
    source_url = display.resolve_recorded_loop_source_url(str(tmp_path))
    assert source_url == "file://" + str(tmp_path / "loop.mp4").replace(" ", "%20")


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
