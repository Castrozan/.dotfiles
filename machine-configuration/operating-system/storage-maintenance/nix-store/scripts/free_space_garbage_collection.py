import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

GIBIBYTE = 1024**3
GENERATION_LINK_PATTERN = re.compile(r"^(?P<profile>.+)-(?P<generation>\d+)-link$")
FUTILE_REPEAT_MARGIN_BYTES = GIBIBYTE
PRUNE_TIMEOUT_SECONDS = 600
COLLECTION_TIMEOUT_SECONDS = 4 * 3600


@dataclass(frozen=True)
class Thresholds:
    minimum_free_bytes: int
    target_free_bytes: int


@dataclass(frozen=True)
class Decision:
    collect: bool
    bytes_to_free: int
    reason: str


def decide(
    free_bytes: int,
    thresholds: Thresholds,
    free_bytes_after_previous_collection: int | None,
) -> Decision:
    if free_bytes >= thresholds.minimum_free_bytes:
        return Decision(False, 0, "free space is above the minimum")
    if (
        free_bytes_after_previous_collection is not None
        and free_bytes
        > free_bytes_after_previous_collection - FUTILE_REPEAT_MARGIN_BYTES
    ):
        return Decision(
            False,
            0,
            "the previous collection already ran at this free space level",
        )
    return Decision(
        True,
        thresholds.target_free_bytes - free_bytes,
        "free space is below the minimum",
    )


def profiles_in_directory(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    names = {entry.name for entry in directory.iterdir() if entry.is_symlink()}
    matches = (GENERATION_LINK_PATTERN.match(name) for name in sorted(names))
    return [
        directory / match["profile"]
        for match in matches
        if match and match["profile"] in names
    ]


def discover_profiles(profile_directories: list[Path]) -> list[Path]:
    return list(
        dict.fromkeys(
            profile
            for directory in profile_directories
            for profile in profiles_in_directory(directory)
        )
    )


def profile_directories(home_root: Path) -> list[Path]:
    system_directories = [
        Path("/nix/var/nix/profiles"),
        Path("/root/.local/state/nix/profiles"),
    ]
    per_user_root = Path("/nix/var/nix/profiles/per-user")
    per_user_directories = (
        sorted(path for path in per_user_root.iterdir() if path.is_dir())
        if per_user_root.is_dir()
        else []
    )
    home_directories = (
        sorted(
            home / ".local/state/nix/profiles"
            for home in home_root.iterdir()
            if home.is_dir()
        )
        if home_root.is_dir()
        else []
    )
    return system_directories + per_user_directories + home_directories


def read_previous_free_bytes(state_file: Path) -> int | None:
    try:
        return int(state_file.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None


def prune_generations(profile: Path, kept_generations: int, dry_run: bool) -> None:
    command = [
        "nix-env",
        "--profile",
        str(profile),
        "--delete-generations",
        f"+{kept_generations}",
    ]
    if dry_run:
        command.append("--dry-run")
    subprocess.run(command, check=True, timeout=PRUNE_TIMEOUT_SECONDS)


def collect_store_garbage(bytes_to_free: int) -> None:
    subprocess.run(
        ["nix-store", "--gc", "--max-freed", str(bytes_to_free)],
        check=True,
        timeout=COLLECTION_TIMEOUT_SECONDS,
    )


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prune old Nix generations and collect store garbage when free space runs low."
    )
    parser.add_argument("--minimum-free-bytes", type=int, required=True)
    parser.add_argument("--target-free-bytes", type=int, required=True)
    parser.add_argument("--kept-generations", type=int, required=True)
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument("--store-path", type=Path, default=Path("/nix/store"))
    parser.add_argument("--home-root", type=Path, default=Path("/home"))
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def forget_previous_collection_once_recovered(
    arguments: argparse.Namespace, free_bytes: int
) -> None:
    if free_bytes >= arguments.minimum_free_bytes and not arguments.dry_run:
        arguments.state_file.unlink(missing_ok=True)


def prune_every_profile(arguments: argparse.Namespace) -> None:
    for profile in discover_profiles(profile_directories(arguments.home_root)):
        print(
            f"pruning {profile} to the newest {arguments.kept_generations} generations"
        )
        prune_generations(profile, arguments.kept_generations, arguments.dry_run)


def collect_and_record_free_space(
    arguments: argparse.Namespace, bytes_to_free: int
) -> None:
    collect_store_garbage(bytes_to_free)
    free_bytes_after = shutil.disk_usage(arguments.store_path).free
    print(f"free after collection {free_bytes_after / GIBIBYTE:.1f} GiB")
    arguments.state_file.parent.mkdir(parents=True, exist_ok=True)
    arguments.state_file.write_text(f"{free_bytes_after}\n")


def run(arguments: argparse.Namespace) -> None:
    thresholds = Thresholds(arguments.minimum_free_bytes, arguments.target_free_bytes)
    free_bytes = shutil.disk_usage(arguments.store_path).free
    decision = decide(
        free_bytes, thresholds, read_previous_free_bytes(arguments.state_file)
    )
    print(
        f"free {free_bytes / GIBIBYTE:.1f} GiB, minimum {thresholds.minimum_free_bytes / GIBIBYTE:.1f} GiB, "
        f"target {thresholds.target_free_bytes / GIBIBYTE:.1f} GiB: {decision.reason}"
    )
    forget_previous_collection_once_recovered(arguments, free_bytes)
    if not decision.collect:
        return
    prune_every_profile(arguments)
    if arguments.dry_run:
        print(
            f"dry run: would collect up to {decision.bytes_to_free / GIBIBYTE:.1f} GiB of store garbage"
        )
        return
    collect_and_record_free_space(arguments, decision.bytes_to_free)


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    run(parse_arguments())
