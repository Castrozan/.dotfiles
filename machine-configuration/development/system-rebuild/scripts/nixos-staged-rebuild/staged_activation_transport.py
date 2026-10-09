from contextlib import contextmanager

from nixos_rebuild import nix


@contextmanager
def local_activation_transport():
    native_command_prefix = nix.SWITCH_TO_CONFIGURATION_CMD_PREFIX
    nix.SWITCH_TO_CONFIGURATION_CMD_PREFIX = []
    try:
        yield
    finally:
        nix.SWITCH_TO_CONFIGURATION_CMD_PREFIX = native_command_prefix
