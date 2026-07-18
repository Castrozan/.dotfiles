import ambient_canvas_browser as browser
import display_ambient_canvas_loop as display
import render_ambient_canvas_loop as render


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
    record_url = render.build_record_index_url(
        "file:///store/index.html", "http://127.0.0.1:5000/upload", 30, 24
    )
    assert record_url.startswith("file:///store/index.html?")
    assert "record=1" in record_url
    assert "seconds=30" in record_url
    assert "fps=24" in record_url
    assert "uploadUrl=http%3A%2F%2F127.0.0.1%3A5000%2Fupload" in record_url


def test_build_record_browser_arguments_use_throwaway_profile_and_gl():
    arguments = render.build_record_browser_arguments(
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


def test_resolve_index_file_path_is_none_without_environment(monkeypatch):
    monkeypatch.delenv("AMBIENT_CANVAS_INDEX", raising=False)
    assert render.resolve_index_file_path() is None


def test_resolve_index_file_path_returns_existing_asset(monkeypatch, tmp_path):
    index_path = tmp_path / "index.html"
    index_path.write_text("<html></html>")
    monkeypatch.setenv("AMBIENT_CANVAS_INDEX", str(index_path))
    assert render.resolve_index_file_path() == str(index_path)


def test_resolve_player_page_path_sits_next_to_the_index():
    assert (
        display.resolve_player_page_path("/store/web/index.html")
        == "/store/web/player-video.html"
    )


def test_build_display_url_encodes_the_recorded_source():
    display_url = display.build_display_url(
        "/store/web/player-video.html", "file:///state/loop.mp4"
    )
    assert display_url.startswith("file:///store/web/player-video.html?")
    assert "src=file%3A%2F%2F%2Fstate%2Floop.mp4" in display_url


def test_build_display_browser_arguments_open_new_app_with_file_access():
    arguments = display.build_display_browser_arguments(
        "Google Chrome",
        "file:///store/web/player-video.html?src=file%3A%2F%2Floop.mp4",
        "/state/profile",
        (1440, 720, 280, 140),
    )
    assert arguments[:4] == ["open", "-na", "Google Chrome", "--args"]
    assert "--user-data-dir=/state/profile" in arguments
    assert "--allow-file-access-from-files" in arguments
    assert "--window-position=280,140" in arguments
