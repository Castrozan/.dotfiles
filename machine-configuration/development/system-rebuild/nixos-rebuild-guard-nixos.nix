{ pkgs, lib, ... }:
let
  exclusiveRunLock = import ../../../agent-harness/session-control/exclusive-run-lock-package.nix {
    inherit pkgs;
  };
  systemRebuildLockGuard = pkgs.writeShellScript "system-rebuild-lock" (
    builtins.readFile ./scripts/system-rebuild-lock
  );
  guardScript = pkgs.writeShellScript "nixos-rebuild-guard" (
    builtins.readFile ./scripts/nixos-rebuild-guard
  );

  guardedNixosRebuild = pkgs.writeShellScriptBin "nixos-rebuild" ''
    export REAL_NIXOS_REBUILD=${pkgs.nixos-rebuild-ng}/bin/nixos-rebuild-ng
    export SYSTEM_REBUILD_LOCK_GUARD=${systemRebuildLockGuard}
    export EXCLUSIVE_RUN_LOCK_HELPER=${exclusiveRunLock}/libexec/exclusive-run-lock/exclusive-run-lock.sh
    export EXCLUSIVE_RUN_SCOPE_PYTHON=${pkgs.python3}/bin/python3
    exec ${guardScript} "$@"
  '';
in
{
  environment.systemPackages = [ (lib.hiPrio guardedNixosRebuild) ];
}
