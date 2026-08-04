import pathlib
import subprocess

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CHECK_REGISTRY_PATH = REPO_ROOT / "__tests__" / "nix-checks" / "default.nix"


def tracked_repository_paths():
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()


def every_check_module_path():
    return {
        path
        for path in tracked_repository_paths()
        if path.endswith("__tests__/checks.nix")
    }


def check_module_paths_imported_by_another_module(check_module_paths):
    imported_paths = set()
    for tracked_path in tracked_repository_paths():
        if not tracked_path.endswith(".nix"):
            continue
        if tracked_path == "__tests__/nix-checks/default.nix":
            continue
        source_text = (REPO_ROOT / tracked_path).read_text(encoding="utf-8")
        importing_directory = pathlib.PurePosixPath(tracked_path).parent
        for check_module_path in check_module_paths:
            if check_module_path == tracked_path:
                continue
            relative_path = pathlib.posixpath.relpath(
                check_module_path, str(importing_directory)
            )
            if relative_path in source_text or f"./{relative_path}" in source_text:
                imported_paths.add(check_module_path)
    return imported_paths


def check_module_paths_listed_in_the_registry():
    registry_text = CHECK_REGISTRY_PATH.read_text(encoding="utf-8")
    return {
        line.strip().removeprefix("../../")
        for line in registry_text.splitlines()
        if line.strip().startswith("../../") and line.strip().endswith("checks.nix")
    }


def test_every_root_check_module_is_registered_so_its_assertions_actually_run():
    check_module_paths = every_check_module_path()
    root_check_module_paths = check_module_paths - (
        check_module_paths_imported_by_another_module(check_module_paths)
    )
    unregistered_root_modules = (
        root_check_module_paths - check_module_paths_listed_in_the_registry()
    )
    assert not unregistered_root_modules, (
        "these check files sit on disk with live assertions that no module imports "
        "and the registry never lists, so nix flake check never evaluates them and "
        "the module reads as covered while its configuration drifts freely; add each "
        f"to __tests__/nix-checks/default.nix: {sorted(unregistered_root_modules)}"
    )


def test_the_registry_lists_no_check_module_that_has_been_deleted():
    missing_from_disk = check_module_paths_listed_in_the_registry() - (
        every_check_module_path()
    )
    assert not missing_from_disk, (
        "the registry names check files that no longer exist, which makes the whole "
        f"flake check output fail to evaluate: {sorted(missing_from_disk)}"
    )
