{ pkgs, config, ... }:
let
    unstable = import (builtins.fetchTarball "https://github.com/NixOS/nixpkgs-channels/archive/nixos-unstable.tar.gz") {
        config = config.nixpkgs.config;
    };
in {
    environment.systemPackages = with pkgs; [
        cargo
        rustc
        SDL2
        alsa-lib.dev
        code-cursor
        pkg-config
    ];
}
