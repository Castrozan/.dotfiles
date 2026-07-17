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


def test_browser_arguments_open_a_new_app_mode_instance():
    arguments = launcher.build_browser_arguments(
        "Brave Browser", "file:///store/index.html", (1440, 720, 280, 140)
    )
    assert arguments[:4] == ["open", "-na", "Brave Browser", "--args"]
    assert "--app=file:///store/index.html" in arguments
    assert f"--user-data-dir={launcher.AMBIENT_CANVAS_PROFILE_DIRECTORY}" in arguments
    assert "--window-size=1440,720" in arguments
    assert "--window-position=280,140" in arguments


def test_resolve_index_file_url_is_none_without_environment(monkeypatch):
    monkeypatch.delenv("AMBIENT_CANVAS_INDEX", raising=False)
    assert launcher.resolve_index_file_url() is None
