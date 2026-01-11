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
    # ../../nixos/modules/media-streaming # Removed: requires insecure qtwebengine-5.15.19
    ../../nixos/modules/keyd.nix
    ../../nixos/modules/agenix.nix
    ../../nixos/modules/tailscale.nix
    ../../nixos/modules/man-cache.nix
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
    # Force Qt applications to use Wayland
    QT_QPA_PLATFORM = "wayland";
  };

  # Allows running uncompiled binaries from npm, pip and other packages
  programs.nix-ld.enable = true;
  programs.nix-ld.libraries = with pkgs; [
    stdenv.cc.cc
    zlib
    openssl
    curl
  ];

  services.flatpak.enable = true;

  services.openssh = {
    enable = true;
    settings = {
      PermitRootLogin = "no";
      PubkeyAuthentication = true;
    };
  };

  networking.firewall = {
    enable = true;
    allowedTCPPorts = [ 22 ];
  };

  users.users.zanoni.openssh.authorizedKeys.keys = [
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFqWoL9l50EyBgITnUyUhDuodLCRCMGLowmMcos7DJPo phone@android"
  ];

  age.identityPaths = lib.mkIf (builtins.pathExists ../../secrets/id_ed25519_phone.age) [
    "/home/zanoni/.ssh/id_ed25519"
  ];

  age.secrets = lib.mkIf (builtins.pathExists ../../secrets/id_ed25519_phone.age) {
    "id_ed25519_phone" = {
      file = ../../secrets/id_ed25519_phone.age;
      owner = "zanoni";
      mode = "600";
    };
  };
}
