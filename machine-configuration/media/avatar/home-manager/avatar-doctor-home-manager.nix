{
  pkgs,
  lib,
  inputs,
  isNixOS,
  ...
}:
let
  programs = import ../avatar-programs.nix { inherit pkgs lib inputs; };
in
{
  config = lib.mkIf isNixOS {
    home.packages = [
      (import ./avatar-doctor-package.nix {
        inherit pkgs lib;
        commands = [
          programs.transcribe
          pkgs.systemd
        ];
        arguments = "";
      })
    ];
  };
}
