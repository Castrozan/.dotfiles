"""The workspace injector reads one state file and prefixes one command.

It loads on every Bash call an agent makes, so it reads that file with open()
and os.path rather than pathlib, whose import bills urllib.parse, ipaddress
and math to every shell command. These cover the states the file can be in,
because a guard that throws on a missing file would break every Bash call
instead of just declining to inject.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module  # noqa: E402

workspace_directory_injector_handler = import_hyphenated_hook_module(
    "workspace_directory_injector_handler"
)


def point_the_state_file_at(monkeypatch, contents, tmp_path):
    state_file = tmp_path / "workspace-cwd"
    if contents is not None:
        state_file.write_text(contents)
    monkeypatch.setattr(
        workspace_directory_injector_handler, "WORKSPACE_STATE_FILE", str(state_file)
    )


def inject_into(command):
    return workspace_directory_injector_handler.handle(
        {"tool_name": "Bash", "tool_input": {"command": command}}
    )


def test_a_missing_state_file_leaves_the_command_alone(tmp_path, monkeypatch):
    point_the_state_file_at(monkeypatch, None, tmp_path)
    assert inject_into("git status") is None


def test_an_empty_state_file_leaves_the_command_alone(tmp_path, monkeypatch):
    point_the_state_file_at(monkeypatch, "   \n", tmp_path)
    assert inject_into("git status") is None


def test_a_directory_that_no_longer_exists_leaves_the_command_alone(
    tmp_path, monkeypatch
):
    point_the_state_file_at(monkeypatch, str(tmp_path / "gone"), tmp_path)
    assert inject_into("git status") is None


def test_a_recorded_directory_is_prefixed_onto_the_command(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    point_the_state_file_at(monkeypatch, f"{workspace}\n", tmp_path)

    result = inject_into("git status")

    assert result.decision == "allow"
    assert result.updated_input["command"].startswith(f"cd {workspace}")
    assert result.updated_input["command"].endswith("&& git status")


def test_a_home_relative_directory_is_expanded(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "workspace").mkdir()
    point_the_state_file_at(monkeypatch, "~/workspace", tmp_path)

    result = inject_into("ls")

    assert str(tmp_path / "workspace") in result.updated_input["command"]


def test_a_command_that_is_missing_is_not_rewritten(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    point_the_state_file_at(monkeypatch, str(workspace), tmp_path)
    assert inject_into("") is None
