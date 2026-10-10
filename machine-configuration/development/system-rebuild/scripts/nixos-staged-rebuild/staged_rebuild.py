import json
import subprocess
import sys
import tempfile
from pathlib import Path

from staged_command import command_failure_status, run_command
from staged_native import parse_native_options
from staged_sources import (
    read_prepared_request,
    retain_source_roots,
    validate_store_path,
)


def run_staged_rebuild(action, request_path, temporary):
    arguments, sources = read_prepared_request(request_path, action)
    options = parse_native_options(arguments)
    activation_options = json.dumps(
        {
            "action": options.action,
            "profile_name": options.profile_name,
            "specialisation": options.specialisation,
            "install_bootloader": options.install_bootloader,
        }
    )
    source_reference = options.flake_reference.split("#", 1)[0]
    if not source_reference.startswith("path:"):
        raise ValueError("privileged evaluation requires an immutable prefetched flake")
    validate_store_path(source_reference.removeprefix("path:"))
    retain_source_roots(sources, temporary, "source_retention")
    derivation = run_command(
        "evaluation",
        [
            "nix",
            "--extra-experimental-features",
            "nix-command flakes",
            "eval",
            "--raw",
            *options.evaluation_flags,
            "--offline",
            "--no-write-lock-file",
            options.derivation_attribute,
        ],
        True,
    )
    validate_store_path(derivation)
    if not derivation.endswith(".drv"):
        raise ValueError("evaluation did not return a system derivation")
    realization_root = Path(temporary) / "system"
    run_command(
        "realization",
        [
            "nix-store",
            "--realise",
            derivation,
            *options.realization_flags,
            "--add-root",
            realization_root,
            "--indirect",
        ],
    )
    if not realization_root.is_symlink():
        raise ValueError("realization did not create its system GC root")
    system_path = validate_store_path(str(realization_root.resolve()))
    activation_driver = Path(__file__).with_name("staged_activation.py")
    for phase, operation in (
        ("profile_update", "profile"),
        ("activation", "activate"),
    ):
        run_command(
            phase,
            [
                sys.executable,
                activation_driver,
                operation,
                activation_options,
                system_path,
            ],
        )


def main():
    try:
        with tempfile.TemporaryDirectory(
            prefix="dotfiles-rebuild-staged-"
        ) as temporary:
            run_staged_rebuild(sys.argv[1], sys.argv[2], temporary)
        return 0
    except subprocess.CalledProcessError as error:
        return command_failure_status(error)
    except (OSError, ValueError, KeyError) as error:
        print(f"error: staged rebuild failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
