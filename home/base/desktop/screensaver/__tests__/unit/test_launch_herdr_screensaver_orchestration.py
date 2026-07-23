import importlib.util
import pathlib
import subprocess

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


def test_find_workspace_returns_matching_screensaver_label(monkeypatch):
    monkeypatch.setattr(
        launcher,
        "run_herdr_json",
        lambda *arguments: {
            "result": {
                "workspaces": [
                    {"label": "dotfiles", "workspace_id": "w1"},
                    {"label": "screensaver", "workspace_id": "w7"},
                ]
            }
        },
    )
    assert launcher.find_screensaver_workspace_id() == "w7"


def test_find_workspace_returns_none_without_screensaver_label(monkeypatch):
    monkeypatch.setattr(
        launcher,
        "run_herdr_json",
        lambda *arguments: {
            "result": {"workspaces": [{"label": "dotfiles", "workspace_id": "w1"}]}
        },
    )
    assert launcher.find_screensaver_workspace_id() is None


def test_pane_is_running_when_foreground_group_differs_from_shell(monkeypatch):
    monkeypatch.setattr(
        launcher,
        "run_herdr_json",
        lambda *arguments: {
            "result": {
                "process_info": {"foreground_process_group_id": 200, "shell_pid": 100}
            }
        },
    )
    assert launcher.pane_is_running_foreground_process("p1") is True


def test_pane_is_idle_when_foreground_group_equals_shell(monkeypatch):
    monkeypatch.setattr(
        launcher,
        "run_herdr_json",
        lambda *arguments: {
            "result": {
                "process_info": {"foreground_process_group_id": 100, "shell_pid": 100}
            }
        },
    )
    assert launcher.pane_is_running_foreground_process("p1") is False


def test_workspace_running_when_any_pane_is_live(monkeypatch):
    monkeypatch.setattr(
        launcher, "list_workspace_pane_ids", lambda workspace: ["p1", "p2"]
    )
    monkeypatch.setattr(
        launcher, "pane_is_running_foreground_process", lambda pane_id: pane_id == "p2"
    )
    assert launcher.workspace_has_running_screensaver("w7") is True


def test_workspace_not_running_when_all_panes_idle(monkeypatch):
    monkeypatch.setattr(
        launcher, "list_workspace_pane_ids", lambda workspace: ["p1", "p2"]
    )
    monkeypatch.setattr(
        launcher, "pane_is_running_foreground_process", lambda pane_id: False
    )
    assert launcher.workspace_has_running_screensaver("w7") is False


def test_main_focuses_existing_running_screensaver(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning({"herdr"}))
    monkeypatch.setattr(launcher, "find_screensaver_workspace_id", lambda: "w7")
    monkeypatch.setattr(
        launcher, "workspace_has_running_screensaver", lambda workspace: True
    )
    herdr_calls = []
    monkeypatch.setattr(
        launcher, "run_herdr", lambda *arguments: herdr_calls.append(arguments)
    )
    monkeypatch.setattr(
        launcher, "start_screensaver", lambda: herdr_calls.append(("start",))
    )
    assert launcher.main() == 0
    assert herdr_calls == [("workspace", "focus", "w7")]


def test_main_rebuilds_dead_screensaver_workspace(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning({"herdr"}))
    monkeypatch.setattr(launcher, "find_screensaver_workspace_id", lambda: "w7")
    monkeypatch.setattr(
        launcher, "workspace_has_running_screensaver", lambda workspace: False
    )
    herdr_calls = []
    monkeypatch.setattr(
        launcher, "run_herdr", lambda *arguments: herdr_calls.append(arguments)
    )
    monkeypatch.setattr(
        launcher, "start_screensaver", lambda: herdr_calls.append(("start",))
    )
    assert launcher.main() == 0
    assert ("workspace", "close", "w7") in herdr_calls
    assert ("start",) in herdr_calls


def test_main_starts_fresh_when_no_existing_workspace(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning({"herdr"}))
    monkeypatch.setattr(launcher, "find_screensaver_workspace_id", lambda: None)
    started = []
    monkeypatch.setattr(launcher, "run_herdr", lambda *arguments: None)
    monkeypatch.setattr(launcher, "start_screensaver", lambda: started.append(True))
    assert launcher.main() == 0
    assert started == [True]


def test_main_is_a_noop_when_herdr_is_absent(monkeypatch):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning(set()))
    started = []
    monkeypatch.setattr(launcher, "start_screensaver", lambda: started.append(True))
    assert launcher.main() == 0
    assert started == []


def test_main_reports_captured_stderr_and_returns_1_on_failure(monkeypatch, capsys):
    monkeypatch.setattr(launcher.shutil, "which", _which_returning({"herdr"}))

    def failing_lookup():
        raise subprocess.CalledProcessError(
            1,
            ["herdr", "workspace", "list"],
            stderr='{"error":{"code":"server_down"}}',
        )

    monkeypatch.setattr(launcher, "find_screensaver_workspace_id", failing_lookup)
    assert launcher.main() == 1
    captured = capsys.readouterr()
    assert "herdr-screensaver" in captured.err
    assert "server_down" in captured.err
