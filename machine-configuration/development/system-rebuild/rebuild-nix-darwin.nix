{
  pkgs,
  lib,
  config,
  hostname,
  ...
}:
let
  exclusiveRunLock = import ../../../agent-harness/session-control/exclusive-run-lock-package.nix {
    inherit pkgs;
  };
  systemRebuildLockGuard = pkgs.writeShellScript "system-rebuild-lock" (
    builtins.readFile ./scripts/system-rebuild-lock
  );
  guardScript = pkgs.writeShellScript "darwin-rebuild-guard" (
    builtins.readFile ./scripts/darwin-rebuild-guard
  );
  guardedDarwinRebuild = pkgs.writeShellScriptBin "darwin-rebuild" ''
    export REAL_DARWIN_REBUILD=${config.system.build.darwin-rebuild}/bin/darwin-rebuild
    export DARWIN_REBUILD_SHELL=${pkgs.bash}/bin/bash
    export DARWIN_REBUILD_ENTRYPOINT="$0"
    export SYSTEM_REBUILD_LOCK_GUARD=${systemRebuildLockGuard}
    export EXCLUSIVE_RUN_LOCK_HELPER=${exclusiveRunLock}/libexec/exclusive-run-lock/exclusive-run-lock.sh
    export EXCLUSIVE_RUN_SCOPE_PYTHON=${pkgs.python3}/bin/python3
    exec ${guardScript} "$@"
  '';
in
{
  environment.systemPackages = [
    (import ./scripts/rebuild { inherit pkgs hostname; })
    (lib.hiPrio guardedDarwinRebuild)
  ];
}
