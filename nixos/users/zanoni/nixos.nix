#
# NixOS Configuration for zanoni
#
{ lib, ... }:
let
  bashrc = builtins.readFile ../../../.bashrc;
in
{
  imports = [
    # TODO: Change this three to be managed as home programs
    ./packages.nix
    ./unstable-packages.nix
    ./scripts/default.nix
    ./virtualization.nix
    ./steam.nix
  ];

  programs.hyprland = {
    enable = true;
    xwayland.enable = true;
  };

  environment.variables = {
    NIX_PATH = lib.mkDefault "nixpkgs=/nix/var/nix/profiles/per-user/root/channels/nixos";
  };

  # # make `nix repl '<nixpkgs>'` use the same nixpkgs as the one used by this flake.
  # # discard all the default paths, and only use the one from this flake.
  # nix.nixPath = lib.mkForce ["/etc/nix/inputs"];
  # # https://github.com/NixOS/nix/issues/9574
  # nix.settings.nix-path = lib.mkForce "nixpkgs=/etc/nix/inputs/nixpkgs";

  # Global Bash configuration
  # TODO: this is workaround from home/programs/bash.nix
  environment.etc."bashrc".text = bashrc;

  # Define a user account. Don't forget to set a password with ‘passwd’.
  users.users.zanoni = {
    isNormalUser = true;
    description = "zanoni";
    extraGroups = [
      "networkmanager"
      "wheel"
    ];
    packages = [ ];
  };
}
