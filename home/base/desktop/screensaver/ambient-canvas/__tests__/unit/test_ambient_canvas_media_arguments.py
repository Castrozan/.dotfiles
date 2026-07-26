import ambient_canvas_browser as browser
import display_ambient_canvas_loop as display
import recorded_loop_capture_plan as capture_plan
import render_ambient_canvas_loop as render

MEASURED_SOLO_BONSAI_RECORDED_BYTES = 270347
MEASURED_SOLO_BONSAI_DURATION_SECONDS = 30


def test_parse_desktop_bounds_returns_width_and_height():
    assert browser.parse_desktop_bounds("0, 0, 2560, 1440") == (2560, 1440)


def test_parse_desktop_bounds_accounts_for_nonzero_origin():
    assert browser.parse_desktop_bounds("100, 50, 1540, 950") == (1440, 900)


def test_centered_geometry_is_fraction_of_screen_and_centered():
    width, height, left, top = browser.resolve_centered_window_geometry(2000, 1000)
    assert width == 1440
    assert height == 720
    assert left == 280
    assert top == 140


def test_resolve_browser_prefers_chrome_when_both_are_installed(monkeypatch):
    monkeypatch.setattr(
        browser.os.path,
        "isdir",
        lambda path: path
        in ("/Applications/Google Chrome.app", "/Applications/Brave Browser.app"),
    )
    assert browser.resolve_chromium_browser_application() == "Google Chrome"


def test_resolve_browser_falls_back_to_brave_when_chrome_absent(monkeypatch):
    monkeypatch.setattr(
        browser.os.path,
        "isdir",
        lambda path: path == "/Applications/Brave Browser.app",
    )
    assert browser.resolve_chromium_browser_application() == "Brave Browser"


def test_resolve_browser_executable_path_points_inside_the_app_bundle():
    assert (
        browser.resolve_browser_executable_path("Google Chrome")
        == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    )


def test_build_record_index_url_encodes_record_query():
    record_url = capture_plan.build_record_index_url(
        "file:///store/index.html", "http://127.0.0.1:5000/upload", 30, 24
    )
    assert record_url.startswith("file:///store/index.html?")
    assert "record=1" in record_url
    assert "seconds=30" in record_url
    assert "fps=24" in record_url
    assert "uploadUrl=http%3A%2F%2F127.0.0.1%3A5000%2Fupload" in record_url


def test_build_record_index_url_omits_seconds_so_the_playlist_derives_the_length():
    record_url = capture_plan.build_record_index_url(
        "file:///store/index.html", "http://127.0.0.1:5000/upload", None, 30
    )
    assert "seconds=" not in record_url
    assert "record=1" in record_url
    assert "fps=30" in record_url


def test_upload_wait_budget_covers_a_whole_incremental_record_pass():
    assert (
        capture_plan.resolve_upload_wait_budget_seconds()
        == capture_plan.RECORD_PASS_WALL_CLOCK_CEILING_SECONDS
    )


def test_minimum_recorded_bytes_scales_with_the_segment_duration():
    assert (
        capture_plan.resolve_minimum_recorded_bytes(30)
        == 30 * capture_plan.MINIMUM_RECORDED_BYTES_PER_SECOND
    )


def test_the_measured_solo_bonsai_composition_clears_the_minimum_recorded_bytes():
    assert (
        capture_plan.resolve_minimum_recorded_bytes(
            MEASURED_SOLO_BONSAI_DURATION_SECONDS
        )
        < MEASURED_SOLO_BONSAI_RECORDED_BYTES
    )


def test_build_record_browser_arguments_use_throwaway_profile_and_gl():
    arguments = capture_plan.build_record_browser_arguments(
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "file:///store/index.html?record=1",
        "/tmp/throwaway",
        (1440, 720, 280, 140),
    )
    assert arguments[0].endswith("Google Chrome")
    assert "--app=file:///store/index.html?record=1" in arguments
    assert "--user-data-dir=/tmp/throwaway" in arguments
    assert "--window-size=1440,720" in arguments
    assert "--use-gl=angle" in arguments
    assert "--disable-background-timer-throttling" in arguments
    assert "--disable-backgrounding-occluded-windows" in arguments


def test_resolve_index_file_path_is_none_without_environment(monkeypatch):
    monkeypatch.delenv("AMBIENT_CANVAS_INDEX", raising=False)
    assert render.resolve_index_file_path() is None


def test_resolve_index_file_path_returns_existing_asset(monkeypatch, tmp_path):
    index_path = tmp_path / "index.html"
    index_path.write_text("<html></html>")
    monkeypatch.setenv("AMBIENT_CANVAS_INDEX", str(index_path))
    assert render.resolve_index_file_path() == str(index_path)


def test_build_player_process_arguments_pass_binary_then_manifest():
    assert display.build_player_process_arguments(
        "/home/user/.local/bin/ambient-canvas-player", "/state/loop.segments.json"
    ) == ["/home/user/.local/bin/ambient-canvas-player", "/state/loop.segments.json"]
