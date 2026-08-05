import importlib.util
import pathlib

SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "scripts"
    / "launch_herdr_screensaver.py"
)


def _load_launcher_module():
    module_spec = importlib.util.spec_from_file_location(
        "launch_herdr_screensaver", SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


launcher = _load_launcher_module()


def _which_returning(available_executables):
    available = set(available_executables)

    def fake_which(executable):
        return f"/usr/bin/{executable}" if executable in available else None

    return fake_which


def test_start_screensaver_routes_pane_commands_through_precompute_loop(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning({"precompute-loop"}))
    monkeypatch.setattr(
        launcher, "resolve_available_screensaver_commands", lambda: ["equation-art"]
    )
    monkeypatch.setattr(launcher, "create_screensaver_workspace", lambda: ("ws1", "p1"))
    herdr_calls = []
    monkeypatch.setattr(
        launcher, "run_herdr", lambda *arguments: herdr_calls.append(arguments)
    )
    launcher.start_screensaver()
    pane_run_calls = [call for call in herdr_calls if call[:2] == ("pane", "run")]
    assert pane_run_calls == [
        (
            "pane",
            "run",
            "p1",
            f"precompute-loop --seconds {launcher.PRECOMPUTE_LOOP_CAPTURE_SECONDS} "
            "-- equation-art",
        )
    ]


def test_single_command_uses_root_pane_without_splitting(monkeypatch):
    split_calls = []
    monkeypatch.setattr(
        launcher, "split_pane", lambda *arguments: split_calls.append(arguments)
    )
    assert launcher.build_screensaver_panes("p1", 1) == ["p1"]
    assert split_calls == []


def test_two_commands_split_the_right_column_once(monkeypatch):
    split_calls = []

    def fake_split(pane_id, direction, ratio):
        split_calls.append((pane_id, direction, ratio))
        return "pRight"

    monkeypatch.setattr(launcher, "split_pane", fake_split)
    assert launcher.build_screensaver_panes("p1", 2) == ["p1", "pRight"]
    assert split_calls == [("p1", "right", launcher.PRIMARY_LEFT_COLUMN_RATIO)]


def test_three_commands_split_right_then_down(monkeypatch):
    split_calls = []
    split_outputs = iter(["pRight", "pBottom"])

    def fake_split(pane_id, direction, ratio):
        split_calls.append((pane_id, direction, ratio))
        return next(split_outputs)

    monkeypatch.setattr(launcher, "split_pane", fake_split)
    assert launcher.build_screensaver_panes("p1", 3) == ["p1", "pRight", "pBottom"]
    assert split_calls == [
        ("p1", "right", launcher.PRIMARY_LEFT_COLUMN_RATIO),
        ("pRight", "down", launcher.RIGHT_COLUMN_VERTICAL_SPLIT_RATIO),
    ]
