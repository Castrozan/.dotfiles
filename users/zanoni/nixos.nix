#
# NixOS configuration for zanoni
#
{ lib, pkgs, ... }:
let
  bashrc = builtins.readFile ../../.bashrc;
in
{
  imports = [
    ./scripts
    ./pkgs.nix
    ../../nixos/modules/virtualization.nix
    ../../nixos/modules/fonts.nix
    ../../nixos/modules/input-pkgs.nix
    ../../nixos/modules/steam.nix
    ../../nixos/modules/whisper-cpp.nix
    ../../nixos/modules/media-streaming
  ];

  users.users.zanoni = {
    isNormalUser = true;
    description = "zanoni";
    extraGroups = [
      "networkmanager"
      "wheel"
    ];
    shell = pkgs.fish;
  };

  # Global Bash configuration
  # TODO: this is workaround from home/packages/bash.nix
  environment.etc."bashrc".text = bashrc;

  # More hyprland configuration in home/hyprland.nix
  programs.hyprland = {
    enable = true;
    xwayland.enable = true;
  };

  # Enable fish globally so it's registered in /etc/shells and available as a login shell
  programs.fish.enable = true;

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

  # Enable Flatpak
  services.flatpak.enable = true;
}
