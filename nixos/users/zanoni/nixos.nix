#
# NixOS configuration for zanoni
#
{ lib, pkgs, ... }:
let
  bashrc = builtins.readFile ../../../.bashrc;
in
{
  imports = [
    ./system-packages.nix
    ./pkgs.nix
    ./unstable-packages.nix
    ./scripts/default.nix
    ./virtualization.nix
    ./programs/steam.nix
    ./programs/whisper-cpp.nix
  ];

  users.users.zanoni = {
    isNormalUser = true;
    description = "zanoni";
    extraGroups = [
      "networkmanager"
      "wheel"
    ];
  };

  # Global Bash configuration
  # TODO: this is workaround from home/programs/bash.nix
  environment.etc."bashrc".text = bashrc;

  # More hyprland configuration in home/hyprland.nix
  programs.hyprland = {
    enable = true;
    xwayland.enable = true;
  };

  # TODO: review this. Which path configuration is better?
  # make `nix repl '<nixpkgs>'` use the same nixpkgs as the one used by this flake.
  # # discard all the default paths, and only use the one from this flake.
  # nix.nixPath = lib.mkForce ["/etc/nix/inputs"];
  # # https://github.com/NixOS/nix/issues/9574
  # nix.settings.nix-path = lib.mkForce "nixpkgs=/etc/nix/inputs/nixpkgs";
  environment.variables = {
    NIX_PATH = lib.mkDefault "nixpkgs=/nix/var/nix/profiles/per-user/root/channels/nixos";
  };

  # Allows running uncompiled binaries from npm, pip and other packages
  programs.nix-ld.enable = true;
  programs.nix-ld.libraries = with pkgs; [
    stdenv.cc.cc
    zlib
    openssl
    curl
  ];
}
