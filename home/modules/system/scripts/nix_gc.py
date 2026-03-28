import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_GENERATIONS_TO_KEEP = 3
NIX_DAEMON_PROFILE = Path("/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh")
HOME_MANAGER_PROFILE_PATH = (
    Path.home() / ".local" / "state" / "nix" / "profiles" / "home-manager"
)
SYSTEM_PROFILE_PATH = Path("/nix/var/nix/profiles/system")


def ensure_nix_in_path_or_source_daemon_profile() -> bool:
    if shutil.which("nix-collect-garbage"):
        return True
    if NIX_DAEMON_PROFILE.is_file():
        result = subprocess.run(
            ["bash", "-c", f". {NIX_DAEMON_PROFILE} && env"],
            capture_output=True,
            text=True,
        )
        for line in result.stdout.splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                if key == "PATH":
                    os.environ["PATH"] = value
        return shutil.which("nix-collect-garbage") is not None
    return False


def resolve_nix_collect_garbage_path() -> str:
    path = shutil.which("nix-collect-garbage")
    return path if path else "nix-collect-garbage"


def compute_generations_to_remove(
    generations_to_keep: int, all_generation_ids: list[str]
) -> list[str]:
    count_to_remove = len(all_generation_ids) - generations_to_keep
    if count_to_remove <= 0:
        return []
    return all_generation_ids[:count_to_remove]


def print_dry_run_generations(generations: list[str]) -> None:
    print("   [DRY RUN] Would remove generations:")
    for generation_id in generations:
        print(f"     - {generation_id}")


def list_nix_env_generations(profile_path: str, sudo: bool = False) -> list[str]:
    command = ["nix-env", "--profile", profile_path, "--list-generations"]
    if sudo:
        command = ["sudo"] + command
    result = subprocess.run(command, capture_output=True, text=True)
    generation_ids = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if parts and parts[0].isdigit():
            generation_ids.append(parts[0])
    return generation_ids


def delete_nix_env_generations(
    profile_path: str,
    generations_to_remove: list[str],
    sudo: bool = False,
    dry_run: bool = False,
) -> None:
    if dry_run:
        print_dry_run_generations(generations_to_remove)
        return
    for generation_id in generations_to_remove:
        print(f"   Removing generation {generation_id}")
        command = [
            "nix-env",
            "--profile",
            profile_path,
            "--delete-generations",
            generation_id,
        ]
        if sudo:
            command = ["sudo"] + command
        subprocess.run(command, capture_output=True)


def clean_home_manager_generations(generations_to_keep: int, dry_run: bool) -> None:
    print(f">> Home-manager generations (keeping {generations_to_keep})...")

    if shutil.which("home-manager"):
        clean_home_manager_generations_via_cli(generations_to_keep, dry_run)
    elif HOME_MANAGER_PROFILE_PATH.exists():
        all_ids = list_nix_env_generations(str(HOME_MANAGER_PROFILE_PATH))
        to_remove = compute_generations_to_remove(generations_to_keep, all_ids)
        if not to_remove:
            print("   Nothing to remove")
        else:
            print(f"   Removing {len(to_remove)} generation(s)")
            delete_nix_env_generations(
                str(HOME_MANAGER_PROFILE_PATH), to_remove, dry_run=dry_run
            )
    else:
        print("   No home-manager profile found, skipping")
    print()


def clean_home_manager_generations_via_cli(
    generations_to_keep: int, dry_run: bool
) -> None:
    result = subprocess.run(
        ["home-manager", "generations"],
        capture_output=True,
        text=True,
    )
    all_generation_ids = []
    for line in result.stdout.splitlines():
        if ": id " in line:
            generation_id = line.split(": id ")[1].split()[0]
            all_generation_ids.append(generation_id)

    generations_to_remove = compute_generations_to_remove(
        generations_to_keep, all_generation_ids
    )

    if not generations_to_remove:
        print("   Nothing to remove")
        return

    print(f"   Removing {len(generations_to_remove)} generation(s)")

    if dry_run:
        print_dry_run_generations(generations_to_remove)
    else:
        for generation_id in generations_to_remove:
            print(f"   Removing generation {generation_id}")
            subprocess.run(
                ["home-manager", "remove-generations", generation_id],
                capture_output=True,
            )


def clean_system_generations(generations_to_keep: int, dry_run: bool) -> None:
    print(f">> System generations (keeping {generations_to_keep})...")

    if not SYSTEM_PROFILE_PATH.exists():
        print("   No system profile found (not NixOS), skipping")
        print()
        return

    all_ids = list_nix_env_generations(str(SYSTEM_PROFILE_PATH), sudo=True)
    to_remove = compute_generations_to_remove(generations_to_keep, all_ids)

    if not to_remove:
        print("   Nothing to remove")
    else:
        print(f"   Removing {len(to_remove)} generation(s)")
        delete_nix_env_generations(
            str(SYSTEM_PROFILE_PATH), to_remove, sudo=True, dry_run=dry_run
        )
    print()


def collect_garbage(dry_run: bool, sudo: bool = False) -> None:
    label = "system" if sudo else "user"
    print(f">> Collecting {label} garbage...")

    nix_gc_path = resolve_nix_collect_garbage_path()

    if dry_run:
        result = subprocess.run(
            ["nix-store", "--gc", "--print-dead"],
            capture_output=True,
            text=True,
        )
        dead_paths_count = len(result.stdout.splitlines())
        print(f"   [DRY RUN] {dead_paths_count} dead store paths would be removed")
    else:
        command = [nix_gc_path]
        if sudo:
            command = ["sudo"] + command
        subprocess.run(command)
    print()


def print_usage() -> None:
    print(
        f"""Usage: nix-gc [OPTIONS]

Delete old Nix generations and collect garbage.

Options:
    -a, --all       Clean user + system (default)
    -u, --user      Clean user only
    -s, --system    Clean system only (requires sudo)
    -k, --keep N    Keep N generations (default: {DEFAULT_GENERATIONS_TO_KEEP})
    -d, --dry-run   Show what would be deleted without deleting
    -h, --help      Show this help message"""
    )


def parse_arguments(
    argv: list[str],
) -> tuple[str, int, bool]:
    scope = "all"
    generations_to_keep = DEFAULT_GENERATIONS_TO_KEEP
    dry_run = False

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("-a", "--all"):
            scope = "all"
        elif arg in ("-u", "--user"):
            scope = "user"
        elif arg in ("-s", "--system"):
            scope = "system"
        elif arg in ("-k", "--keep"):
            i += 1
            if i >= len(argv):
                print("Error: --keep requires a number", file=sys.stderr)
                raise SystemExit(1)
            generations_to_keep = int(argv[i])
        elif arg in ("-d", "--dry-run"):
            dry_run = True
        elif arg in ("-h", "--help"):
            print_usage()
            raise SystemExit(0)
        else:
            print(f"Unknown option: {arg}", file=sys.stderr)
            print_usage()
            raise SystemExit(1)
        i += 1

    return scope, generations_to_keep, dry_run


def main() -> None:
    if not ensure_nix_in_path_or_source_daemon_profile():
        print(
            "Error: nix is not available in PATH and nix-daemon profile was not found.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    scope, generations_to_keep, dry_run = parse_arguments(sys.argv[1:])

    print(f"=== Nix GC (keep {generations_to_keep}) ===")
    print()

    if scope in ("user", "all"):
        clean_home_manager_generations(generations_to_keep, dry_run)
        collect_garbage(dry_run, sudo=False)

    if scope in ("system", "all"):
        clean_system_generations(generations_to_keep, dry_run)
        collect_garbage(dry_run, sudo=True)

    if dry_run:
        print("=== Dry run complete (no changes made) ===")
    else:
        print("=== Done ===")


if __name__ == "__main__":
    main()
