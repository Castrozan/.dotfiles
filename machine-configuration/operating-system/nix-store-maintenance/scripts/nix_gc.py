import os
import shutil
import subprocess
import sys
from pathlib import Path

NIX_DAEMON_PROFILE = Path("/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh")


def ensure_nix_in_path_or_source_daemon_profile() -> bool:
    if shutil.which("nix-collect-garbage"):
        return True
    if not NIX_DAEMON_PROFILE.is_file():
        return False

    result = subprocess.run(
        ["bash", "-c", f". {NIX_DAEMON_PROFILE} && env"],
        capture_output=True,
        text=True,
        check=True,
    )
    for line in result.stdout.splitlines():
        key, separator, value = line.partition("=")
        if separator and key == "PATH":
            os.environ["PATH"] = value
    return shutil.which("nix-collect-garbage") is not None


def resolve_nix_collect_garbage_path() -> str:
    path = shutil.which("nix-collect-garbage")
    return path if path else "nix-collect-garbage"


def collect_garbage(dry_run: bool, sudo: bool = False) -> None:
    label = "system" if sudo else "user"
    print(f">> Cleaning {label} generations and garbage...")

    command_prefix = ["sudo"] if sudo else []
    command = [resolve_nix_collect_garbage_path(), "--delete-old"]
    if dry_run:
        command.append("--dry-run")
    subprocess.run(command_prefix + command, check=True)

    if dry_run:
        result = subprocess.run(
            command_prefix + ["nix-store", "--gc", "--print-dead"],
            capture_output=True,
            text=True,
            check=True,
        )
        dead_paths_count = len(result.stdout.splitlines())
        print(f"   [DRY RUN] {dead_paths_count} dead store paths would be removed")
    print()


def print_usage() -> None:
    print(
        """Usage: nix-gc [OPTIONS]

Delete every old generation from discovered Nix profiles and collect garbage.

Options:
    -a, --all       Clean user + system (default)
    -u, --user      Clean user only
    -s, --system    Clean system only (requires sudo)
    -d, --dry-run   Show what would be deleted without deleting
    -h, --help      Show this help message"""
    )


def parse_arguments(argv: list[str]) -> tuple[str, bool]:
    scope = "all"
    dry_run = False

    for argument in argv:
        if argument in ("-a", "--all"):
            scope = "all"
        elif argument in ("-u", "--user"):
            scope = "user"
        elif argument in ("-s", "--system"):
            scope = "system"
        elif argument in ("-d", "--dry-run"):
            dry_run = True
        elif argument in ("-h", "--help"):
            print_usage()
            raise SystemExit(0)
        else:
            print(f"Unknown option: {argument}", file=sys.stderr)
            print_usage()
            raise SystemExit(1)

    return scope, dry_run


def main() -> None:
    if not ensure_nix_in_path_or_source_daemon_profile():
        print(
            "Error: nix is not available in PATH and nix-daemon profile was not found.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    scope, dry_run = parse_arguments(sys.argv[1:])

    print("=== Nix GC ===")
    print()

    if scope in ("user", "all"):
        collect_garbage(dry_run, sudo=False)

    if scope in ("system", "all"):
        collect_garbage(dry_run, sudo=True)

    if dry_run:
        print("=== Dry run complete (no changes made) ===")
    else:
        print("=== Done ===")


if __name__ == "__main__":
    main()
