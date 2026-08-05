import pathlib
import subprocess

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CHECK_REGISTRY_PATH = (
    REPO_ROOT / "repository" / "verification" / "nix-checks" / "default.nix"
)


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
        if "/__tests__/" in path and path.endswith("checks.nix")
    }


def check_module_paths_imported_by_another_module(check_module_paths):
    imported_paths = set()
    for tracked_path in tracked_repository_paths():
        if not tracked_path.endswith(".nix"):
            continue
        if tracked_path == "repository/verification/nix-checks/default.nix":
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


def automatically_discoverable_check_module_paths():
    return {
        path
        for path in every_check_module_path()
        if pathlib.PurePosixPath(path).name == "checks.nix"
        and pathlib.PurePosixPath(path).parent.name == "__tests__"
    }


def test_every_root_check_module_uses_the_auto_discovered_file_name():
    check_module_paths = every_check_module_path()
    root_check_module_paths = check_module_paths - (
        check_module_paths_imported_by_another_module(check_module_paths)
    )
    undiscoverable_root_modules = (
        root_check_module_paths - automatically_discoverable_check_module_paths()
    )
    assert not undiscoverable_root_modules, (
        "these check files sit on disk with live assertions that no module imports "
        "and their names prevent the registry from discovering them, so nix flake "
        "check never evaluates them and the module reads as covered while its "
        f"configuration drifts freely; rename each to checks.nix: {sorted(undiscoverable_root_modules)}"
    )


def test_the_registry_discovers_check_modules_instead_of_listing_them_by_hand():
    registry_text = CHECK_REGISTRY_PATH.read_text(encoding="utf-8")
    assert "lib.filesystem.listFilesRecursive self.outPath" in registry_text
    hard_coded_check_module_paths = {
        line.strip()
        for line in registry_text.splitlines()
        if line.strip().startswith("../../../") and line.strip().endswith("checks.nix")
    }
    assert not hard_coded_check_module_paths, (
        "the registry must derive check modules from the repository tree so moving "
        "or adding a capability cannot leave checks unevaluated; remove these "
        f"hand-maintained paths: {sorted(hard_coded_check_module_paths)}"
    )
