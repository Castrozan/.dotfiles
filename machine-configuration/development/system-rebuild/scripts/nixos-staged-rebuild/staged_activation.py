import json
import subprocess
import sys
from pathlib import Path

from nixos_rebuild import nix
from nixos_rebuild.models import Action, NixOSRebuildError, Profile

from staged_command import command_failure_status
from staged_activation_transport import local_activation_transport
from staged_sources import validate_store_path


def _execute_native_operation(operation, options, system_path):
    if options["action"] not in ("switch", "boot"):
        raise ValueError("unknown native activation action")
    system = Path(validate_store_path(system_path))
    if operation == "profile":
        nix.set_profile(
            Profile.from_arg(options["profile_name"]),
            system,
            target_host=None,
            sudo=False,
        )
    elif operation == "activate":
        with local_activation_transport():
            nix.switch_to_configuration(
                system,
                Action(options["action"]),
                target_host=None,
                sudo=False,
                install_bootloader=options["install_bootloader"],
                specialisation=options["specialisation"],
            )
    else:
        raise ValueError("unknown native activation operation")


def main():
    try:
        operation, activation_options, system_path = sys.argv[1:4]
        options = json.loads(activation_options)
        _execute_native_operation(operation, options, system_path)
        return 0
    except subprocess.CalledProcessError as error:
        return command_failure_status(error)
    except (OSError, ValueError, KeyError, NixOSRebuildError) as error:
        print(f"error: native activation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
