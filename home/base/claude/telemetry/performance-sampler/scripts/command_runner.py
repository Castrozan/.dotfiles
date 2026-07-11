import os
import shutil
import subprocess

SYSTEM_BINARY_SEARCH_DIRECTORIES = [
    "/usr/bin",
    "/bin",
    "/usr/sbin",
    "/sbin",
    "/opt/homebrew/bin",
    "/run/current-system/sw/bin",
]


def build_command_environment() -> dict:
    command_environment = dict(os.environ)
    home_directory = os.path.expanduser("~")
    current_user_name = os.environ.get("USER", "")
    augmented_search_directories = SYSTEM_BINARY_SEARCH_DIRECTORIES + [
        os.path.join(home_directory, ".nix-profile", "bin"),
        f"/etc/profiles/per-user/{current_user_name}/bin",
    ]
    existing_search_path = command_environment.get("PATH", "")
    if existing_search_path:
        augmented_search_directories.append(existing_search_path)
    command_environment["PATH"] = os.pathsep.join(augmented_search_directories)
    return command_environment


def run_command_capturing_stdout(argument_vector, timeout_seconds: float = 20.0) -> str:
    completed_process = subprocess.run(
        argument_vector,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        env=build_command_environment(),
        check=False,
    )
    return completed_process.stdout


def resolve_executable_path(executable_name: str):
    return shutil.which(executable_name, path=build_command_environment()["PATH"])
