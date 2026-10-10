{ pkgs, lib, ... }:
let
  systemRebuildLockGuard = import ./system-rebuild-lock-package.nix {
    inherit pkgs;
  };
  guardScript = pkgs.writeShellScript "nixos-rebuild-guard" (
    builtins.readFile ./scripts/nixos-rebuild-guard
  );

  guardedNixosRebuild = pkgs.writeShellScriptBin "nixos-rebuild" ''
    export REAL_NIXOS_REBUILD=${pkgs.nixos-rebuild-ng}/bin/nixos-rebuild-ng
    export SYSTEM_REBUILD_LOCK_GUARD=${systemRebuildLockGuard}
    exec ${guardScript} "$@"
  '';
in
{
  environment.systemPackages = [ (lib.hiPrio guardedNixosRebuild) ];
}
