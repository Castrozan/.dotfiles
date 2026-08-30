import ambient_canvas_browser as browser
import display_ambient_canvas_loop as display
import recorded_loop_capture_plan as capture_plan
import render_ambient_canvas_loop as render

MEASURED_SOLO_BONSAI_RECORDED_BYTES = 270347
MEASURED_SOLO_BONSAI_DURATION_SECONDS = 30


def test_resolve_browser_prefers_chrome_when_both_are_installed(monkeypatch):
    monkeypatch.setattr(browser, "resolve_platform", lambda: "darwin")
    monkeypatch.setattr(
        browser.os.path,
        "isdir",
        lambda path: path
        in ("/Applications/Google Chrome.app", "/Applications/Brave Browser.app"),
    )
    assert browser.resolve_chromium_browser_application() == "Google Chrome"


def test_resolve_browser_falls_back_to_brave_when_chrome_absent(monkeypatch):
    monkeypatch.setattr(browser, "resolve_platform", lambda: "darwin")
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


def test_resolve_browser_on_linux_uses_the_which_result(monkeypatch):
    monkeypatch.setattr(browser, "resolve_platform", lambda: "linux")
    monkeypatch.setattr(
        browser.shutil, "which", lambda name: f"/run/current-system/sw/bin/{name}"
    )
    assert (
        browser.resolve_chromium_browser_application()
        == "/run/current-system/sw/bin/google-chrome-stable"
    )
    assert (
        browser.resolve_browser_executable_path("/run/current-system/sw/bin/chromium")
        == "/run/current-system/sw/bin/chromium"
    )


def test_build_record_index_url_encodes_record_query():
    record_url = capture_plan.build_record_index_url(
        "file:///store/index.html",
        "http://127.0.0.1:5000/upload",
        30,
        24,
        (1920, 1080),
        "#241010",
    )
    assert record_url.startswith("file:///store/index.html?")
    assert "record=1" in record_url
    assert "seconds=30" in record_url
    assert "fps=24" in record_url
    assert "width=1920" in record_url
    assert "height=1080" in record_url
    assert "themeBackground=%23241010" in record_url
    assert "uploadUrl=http%3A%2F%2F127.0.0.1%3A5000%2Fupload" in record_url


def test_build_record_index_url_omits_seconds_so_the_playlist_derives_the_length():
    record_url = capture_plan.build_record_index_url(
        "file:///store/index.html",
        "http://127.0.0.1:5000/upload",
        None,
        30,
        (1662, 1080),
        "#241010",
    )
    assert "seconds=" not in record_url
    assert "record=1" in record_url
    assert "fps=30" in record_url
    assert "width=1662" in record_url


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


def test_build_record_browser_arguments_use_throwaway_profile_and_gl(monkeypatch):
    monkeypatch.setattr(
        capture_plan.ambient_canvas_browser, "resolve_platform", lambda: "linux"
    )
    arguments = capture_plan.build_record_browser_arguments(
        "/usr/bin/google-chrome-stable",
        "file:///store/index.html?record=1",
        "/tmp/throwaway",
        (1440, 720, 280, 140),
    )
    assert arguments[0].endswith("google-chrome-stable")
    assert "--app=file:///store/index.html?record=1" in arguments
    assert "--user-data-dir=/tmp/throwaway" in arguments
    assert "--window-size=1440,720" in arguments
    assert "--use-gl=angle" in arguments
    assert "--disable-accelerated-video-decode" in arguments
    assert "--disable-background-timer-throttling" in arguments
    assert "--disable-backgrounding-occluded-windows" in arguments


def test_build_record_browser_arguments_on_darwin_keep_hardware_video_decode(
    monkeypatch,
):
    monkeypatch.setattr(
        capture_plan.ambient_canvas_browser, "resolve_platform", lambda: "darwin"
    )
    arguments = capture_plan.build_record_browser_arguments(
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "file:///store/index.html?record=1",
        "/tmp/throwaway",
        (1440, 720, 280, 140),
    )
    assert "--use-gl=angle" in arguments
    assert "--disable-accelerated-video-decode" not in arguments


def test_resolve_index_file_path_is_none_without_environment(monkeypatch):
    monkeypatch.delenv("AMBIENT_CANVAS_INDEX", raising=False)
    assert render.resolve_index_file_path() is None


def test_resolve_index_file_path_returns_existing_asset(monkeypatch, tmp_path):
    index_path = tmp_path / "index.html"
    index_path.write_text("<html></html>")
    monkeypatch.setenv("AMBIENT_CANVAS_INDEX", str(index_path))
    assert render.resolve_index_file_path() == str(index_path)


def test_build_player_process_arguments_pass_binary_then_manifest_then_dwell():
    assert display.build_player_process_arguments(
        "/home/user/.local/bin/ambient-canvas-player",
        "/state/loops/1660x1080/loop.segments.json",
        "/state/playback-dwell-seconds",
    ) == [
        "/home/user/.local/bin/ambient-canvas-player",
        "/state/loops/1660x1080/loop.segments.json",
        "/state/playback-dwell-seconds",
    ]
