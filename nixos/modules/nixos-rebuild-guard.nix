{ pkgs, lib, ... }:
let
  guardScript = pkgs.writeShellScript "nixos-rebuild-guard" (
    builtins.readFile ./scripts/nixos-rebuild-guard
  );

  guardedNixosRebuild = pkgs.writeShellScriptBin "nixos-rebuild" ''
    export REAL_NIXOS_REBUILD=${pkgs.nixos-rebuild-ng}/bin/nixos-rebuild
    exec ${guardScript} "$@"
  '';
in
{
  environment.systemPackages = [ (lib.hiPrio guardedNixosRebuild) ];
}
