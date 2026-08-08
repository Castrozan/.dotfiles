from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

HYPRLAND_ENV_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "program-configuration"
    / "bash_hyprland_env.sh"
)

GRAPHICAL_SESSION_ENVIRONMENT = {
    "WAYLAND_DISPLAY": "wayland-1",
    "DISPLAY": ":0",
    "XAUTHORITY": "/run/user/1000/xwayland-auth",
    "XDG_CURRENT_DESKTOP": "Hyprland",
    "HYPRLAND_INSTANCE_SIGNATURE": "0123456789abcdef_1783870029_242854003",
}


def install_fake_systemd_user_manager(directory: Path) -> None:
    reported_environment = directory / "user-manager-environment"
    reported_environment.write_text(
        "PATH=/run/current-system/sw/bin\n"
        + "".join(
            f"{name}={value}\n" for name, value in GRAPHICAL_SESSION_ENVIRONMENT.items()
        )
    )
    fake_systemctl = directory / "systemctl"
    fake_systemctl.write_text(
        "#!/usr/bin/env bash\n"
        '[ "$1" = "--user" ] && [ "$2" = "show-environment" ] || exit 1\n'
        f"exec cat {reported_environment}\n"
    )
    fake_systemctl.chmod(0o755)


def install_fake_hyprctl_reporting_a_reachable_compositor(directory: Path) -> None:
    fake_hyprctl = directory / "hyprctl"
    fake_hyprctl.write_text("#!/usr/bin/env bash\nexit 0\n")
    fake_hyprctl.chmod(0o755)


def source_script_in_interactive_shell(
    shell_environment: dict[str, str], fake_binary_directory: Path
) -> dict[str, str]:
    bash = shutil.which("bash") or "/bin/bash"
    child_environment = dict(shell_environment)
    child_environment["HOME"] = os.path.expanduser("~")
    child_environment["PATH"] = f"{fake_binary_directory}:{os.environ.get('PATH', '')}"
    completed = subprocess.run(
        [bash, "--norc", "--noprofile", "-i", "-c", f". {HYPRLAND_ENV_SCRIPT}; env"],
        env=child_environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        pytest.fail(f"sourcing {HYPRLAND_ENV_SCRIPT} failed: {completed.stderr}")
    resulting_environment = {}
    for line in completed.stdout.splitlines():
        name, separator, value = line.partition("=")
        if separator:
            resulting_environment[name] = value
    return resulting_environment


def test_herdr_pane_shell_recovers_the_graphical_session_environment(tmp_path):
    install_fake_systemd_user_manager(tmp_path)
    install_fake_hyprctl_reporting_a_reachable_compositor(tmp_path)
    recovered = source_script_in_interactive_shell({"HERDR_ENV": "1"}, tmp_path)
    for name, value in GRAPHICAL_SESSION_ENVIRONMENT.items():
        assert recovered.get(name) == value, (
            f"a herdr pane shell started without a display must recover {name} from the "
            f"systemd user manager, otherwise every clipboard, screenshot and hyprctl "
            f"call inside the pane fails; got {recovered.get(name)!r}"
        )


def test_shell_that_already_has_a_display_keeps_its_own_values(tmp_path):
    install_fake_systemd_user_manager(tmp_path)
    preexisting = {"HERDR_ENV": "1", "WAYLAND_DISPLAY": "wayland-9", "DISPLAY": ":9"}
    resulting = source_script_in_interactive_shell(preexisting, tmp_path)
    assert resulting.get("WAYLAND_DISPLAY") == "wayland-9"
    assert resulting.get("DISPLAY") == ":9"


def test_shell_without_a_user_manager_leaves_the_environment_untouched(tmp_path):
    absent_manager_directory = tmp_path / "empty"
    absent_manager_directory.mkdir()
    resulting = source_script_in_interactive_shell(
        {"HERDR_ENV": "1"}, absent_manager_directory
    )
    assert "WAYLAND_DISPLAY" not in resulting
