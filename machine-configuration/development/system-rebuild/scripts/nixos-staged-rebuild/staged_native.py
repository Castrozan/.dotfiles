from dataclasses import dataclass

from nixos_rebuild import parse_args
from nixos_rebuild.models import Flake
from nixos_rebuild.utils import dict_to_flags


@dataclass(frozen=True)
class NativeRebuildOptions:
    action: str
    flake_reference: str
    derivation_attribute: str
    profile_name: str
    specialisation: str | None
    install_bootloader: bool
    input_overrides: tuple[tuple[str, str], ...]
    archive_flags: tuple[str, ...]
    evaluation_flags: tuple[str, ...]
    realization_flags: tuple[str, ...]


def parse_native_options(arguments):
    parsed, grouped = parse_args(["nixos-rebuild", *arguments])
    unsupported_modes = (
        "rollback",
        "build_host",
        "target_host",
        "file",
        "attr",
        "upgrade",
        "upgrade_all",
        "impure",
        "commit_lock_file",
        "recreate_lock_file",
        "update_input",
        "refresh",
    )
    if parsed.action not in ("switch", "boot") or not isinstance(parsed.flake, str):
        raise ValueError("staged rebuild requires a local flake and switch or boot")
    if any(getattr(parsed, mode, None) for mode in unsupported_modes):
        raise ValueError("staged rebuild requires an immutable local flake")
    if parsed.action == "boot" and parsed.specialisation:
        raise ValueError("boot cannot activate a specialisation")
    archive_flags = dict_to_flags(grouped.flake_common_flags)
    evaluation_flags = [
        *archive_flags,
        *dict_to_flags({"show_trace": parsed.show_trace, "include": parsed.include}),
    ]
    realization_flags = {
        "max_jobs": "1",
        "cores": "1",
        **{
            name: value
            for name, value in grouped.build_flags.items()
            if value is not None
            and name not in ("print_build_logs", "no_link", "include")
        },
    }
    return NativeRebuildOptions(
        action=parsed.action,
        flake_reference=parsed.flake,
        derivation_attribute=Flake.parse(parsed.flake).to_attr(
            "config", "system", "build", "toplevel", "drvPath"
        ),
        profile_name=parsed.profile_name,
        specialisation=parsed.specialisation,
        install_bootloader=parsed.install_bootloader,
        input_overrides=tuple(
            tuple(override)
            for override in grouped.flake_common_flags.get("override_input") or ()
        ),
        archive_flags=tuple(archive_flags),
        evaluation_flags=tuple(evaluation_flags),
        realization_flags=tuple(dict_to_flags(realization_flags)),
    )
