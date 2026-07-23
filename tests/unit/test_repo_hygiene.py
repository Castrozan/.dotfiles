import os
import pathlib
import re

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
THIS_TEST_FILE = pathlib.Path(__file__).resolve()


SKIP_DIRECTORY_NAMES = {
    ".git",
    "node_modules",
    "result",
    "__pycache__",
    ".direnv",
    ".pytest_cache",
    ".mypy_cache",
    ".devenv",
    "private-config",
    ".worktrees",
    ".deep-work",
}


def _walk_repo_paths_filtered():
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [
            directory
            for directory in dirs
            if directory not in SKIP_DIRECTORY_NAMES
            and not directory.startswith("result-")
        ]
        root_path = pathlib.Path(root)
        for file_name in files:
            yield root_path / file_name


def _collect_files_with_extension(extension):
    return [path for path in _walk_repo_paths_filtered() if path.suffix == extension]


def _path_is_in_chise_host_tree(path):
    relative = path.relative_to(REPO_ROOT).as_posix()
    return (
        relative.startswith("hosts/chise/")
        or relative == "hosts/chise"
        or relative.startswith("home/hosts/linux/chise/")
        or relative == "home/hosts/linux/chise.nix"
    )


HARDCODED_NON_LUCAS_HOME_PATTERN = re.compile(r"/home/zanoni(?:/|\b)")


def _is_acceptable_zanoni_home_reference(path):
    relative = path.relative_to(REPO_ROOT).as_posix()
    if _path_is_in_chise_host_tree(path):
        return True
    if relative.startswith("nixos/"):
        return True
    if relative.startswith("hosts/"):
        return True
    return False


@pytest.fixture(scope="module")
def all_nix_files():
    return _collect_files_with_extension(".nix")


@pytest.fixture(scope="module")
def all_shell_files():
    return [
        path for path in _walk_repo_paths_filtered() if path.suffix in {".sh", ".bash"}
    ]


@pytest.fixture(scope="module")
def all_python_files():
    return _collect_files_with_extension(".py")


def test_no_hardcoded_zanoni_home_paths_outside_zanoni_user_tree(
    all_nix_files, all_python_files, all_shell_files
):
    offenders = []
    for path in [*all_nix_files, *all_python_files, *all_shell_files]:
        if path == THIS_TEST_FILE:
            continue
        if _is_acceptable_zanoni_home_reference(path):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            if HARDCODED_NON_LUCAS_HOME_PATTERN.search(line):
                offenders.append(f"{path}:{line_number}: {line.strip()}")

    assert not offenders, (
        "Hardcoded /home/zanoni/ path found outside the chise host tree. "
        "Use config.home.homeDirectory or $HOME instead.\n" + "\n".join(offenders)
    )


def _collect_symlinks_under(directory):
    return [path for path in directory.rglob("*") if path.is_symlink()]


def test_eval_config_symlinks_resolve():
    eval_config_directory = REPO_ROOT / "agents" / "evals" / "config"
    if not eval_config_directory.exists():
        pytest.skip("agents/evals/config not present")

    broken_symlinks = []
    for symlink_path in _collect_symlinks_under(eval_config_directory):
        if not symlink_path.exists():
            broken_symlinks.append(f"{symlink_path} -> {os.readlink(symlink_path)}")

    assert not broken_symlinks, (
        "Broken symlink(s) under agents/evals/config. The eval framework "
        "imports these YAML files; a broken link crashes --list and "
        "--save-baseline.\n" + "\n".join(broken_symlinks)
    )


REFERENCED_SCRIPT_PATTERN = re.compile(r"\b(launch-project-agent)\b")


def test_no_references_to_removed_launch_project_agent_script():
    extensions_to_check = {".nix", ".py", ".sh", ".md"}
    offenders = []
    for path in _walk_repo_paths_filtered():
        if path == THIS_TEST_FILE:
            continue
        if path.suffix not in extensions_to_check:
            continue
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative.startswith(".deep-work/"):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            if REFERENCED_SCRIPT_PATTERN.search(line):
                offenders.append(f"{path}:{line_number}: {line.strip()}")

    assert not offenders, (
        "References to launch-project-agent found. That script was removed "
        "when persistent project agents became declarative. Update the "
        "reference to mention claude-project-agents.nix declaration "
        "instead.\n" + "\n".join(offenders)
    )
