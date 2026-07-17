import importlib.util
import pathlib

SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2] / "scripts" / "launch_ambient_canvas.py"
)


def _load_launcher_module():
    module_spec = importlib.util.spec_from_file_location(
        "launch_ambient_canvas", SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


launcher = _load_launcher_module()


def test_parse_desktop_bounds_returns_width_and_height():
    assert launcher.parse_desktop_bounds("0, 0, 2560, 1440") == (2560, 1440)


def test_parse_desktop_bounds_accounts_for_nonzero_origin():
    assert launcher.parse_desktop_bounds("100, 50, 1540, 950") == (1440, 900)


def test_centered_geometry_is_fraction_of_screen_and_centered():
    width, height, left, top = launcher.resolve_centered_window_geometry(2000, 1000)
    assert width == 1440
    assert height == 720
    assert left == 280
    assert top == 140


def test_resolve_browser_prefers_chrome_when_both_are_installed(monkeypatch):
    monkeypatch.setattr(
        launcher.os.path,
        "isdir",
        lambda path: path
        in ("/Applications/Google Chrome.app", "/Applications/Brave Browser.app"),
    )
    assert launcher.resolve_chromium_browser_application() == "Google Chrome"


def test_resolve_browser_falls_back_to_brave_when_chrome_absent(monkeypatch):
    monkeypatch.setattr(
        launcher.os.path,
        "isdir",
        lambda path: path == "/Applications/Brave Browser.app",
    )
    assert launcher.resolve_chromium_browser_application() == "Brave Browser"


def test_browser_arguments_open_a_new_app_mode_instance():
    arguments = launcher.build_browser_arguments(
        "Google Chrome", "file:///store/index.html", (1440, 720, 280, 140)
    )
    assert arguments[:4] == ["open", "-na", "Google Chrome", "--args"]
    assert "--app=file:///store/index.html" in arguments
    assert f"--user-data-dir={launcher.AMBIENT_CANVAS_PROFILE_DIRECTORY}" in arguments
    assert "--window-size=1440,720" in arguments
    assert "--window-position=280,140" in arguments


def test_resolve_index_file_url_is_none_without_environment(monkeypatch):
    monkeypatch.delenv("AMBIENT_CANVAS_INDEX", raising=False)
    assert launcher.resolve_index_file_url() is None


def test_resolve_index_file_url_builds_file_url_for_existing_asset(
    monkeypatch, tmp_path
):
    index_path = tmp_path / "index.html"
    index_path.write_text("<html></html>")
    monkeypatch.setenv("AMBIENT_CANVAS_INDEX", str(index_path))
    assert launcher.resolve_index_file_url() == "file://" + str(index_path)


def test_resolve_index_file_url_is_none_when_asset_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("AMBIENT_CANVAS_INDEX", str(tmp_path / "absent.html"))
    assert launcher.resolve_index_file_url() is None


def test_read_screen_dimensions_falls_back_when_osascript_absent(monkeypatch):
    def raise_file_not_found(arguments, **_keyword_arguments):
        raise FileNotFoundError("osascript not present")

    monkeypatch.setattr(launcher.subprocess, "run", raise_file_not_found)
    assert launcher.read_screen_dimensions() == (
        launcher.FALLBACK_SCREEN_WIDTH,
        launcher.FALLBACK_SCREEN_HEIGHT,
    )


def test_read_screen_dimensions_falls_back_when_bounds_unparsable(monkeypatch):
    import types

    monkeypatch.setattr(
        launcher.subprocess,
        "run",
        lambda arguments, **_keyword_arguments: types.SimpleNamespace(
            stdout="not,bounds"
        ),
    )
    assert launcher.read_screen_dimensions() == (
        launcher.FALLBACK_SCREEN_WIDTH,
        launcher.FALLBACK_SCREEN_HEIGHT,
    )


def test_read_screen_dimensions_parses_well_formed_bounds(monkeypatch):
    import types

    monkeypatch.setattr(
        launcher.subprocess,
        "run",
        lambda arguments, **_keyword_arguments: types.SimpleNamespace(
            stdout="0, 0, 2560, 1440\n"
        ),
    )
    assert launcher.read_screen_dimensions() == (2560, 1440)


def test_main_returns_error_when_no_chromium_browser_is_installed(monkeypatch):
    monkeypatch.setattr(launcher, "resolve_chromium_browser_application", lambda: None)
    assert launcher.main() == 1


def test_main_returns_error_when_web_assets_are_missing(monkeypatch):
    monkeypatch.setattr(
        launcher, "resolve_chromium_browser_application", lambda: "Google Chrome"
    )
    monkeypatch.setattr(launcher, "resolve_index_file_url", lambda: None)
    assert launcher.main() == 1


def test_main_launches_the_configured_browser_on_the_success_path(monkeypatch):
    monkeypatch.setattr(
        launcher, "resolve_chromium_browser_application", lambda: "Google Chrome"
    )
    monkeypatch.setattr(
        launcher, "resolve_index_file_url", lambda: "file:///store/index.html"
    )
    monkeypatch.setattr(launcher, "read_screen_dimensions", lambda: (2000, 1000))
    monkeypatch.setattr(
        launcher.os, "makedirs", lambda *args, **keyword_arguments: None
    )
    captured_arguments = {}

    def capture_subprocess_run(arguments, **_keyword_arguments):
        captured_arguments["value"] = arguments

    monkeypatch.setattr(launcher.subprocess, "run", capture_subprocess_run)
    assert launcher.main() == 0
    assert captured_arguments["value"][:4] == [
        "open",
        "-na",
        "Google Chrome",
        "--args",
    ]
    assert "--app=file:///store/index.html" in captured_arguments["value"]
