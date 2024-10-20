#
# NixOS Configuration for zanoni
#
let
  bashrc = builtins.readFile ../../../.bashrc;
in
{

  # Global Bash configuration
  # TODO: this is workaroun from home/programs/bash.nix
  environment.etc."bashrc".text = bashrc;

  users.users.zanoni = {
    # Some nixos config for the user
  };
}
