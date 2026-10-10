{ pkgs }:
let
  exclusiveRunLock = import ../../../agent-harness/session-control/exclusive-run-lock-package.nix {
    inherit pkgs;
  };
  systemRebuildLockGuard = pkgs.writeShellScript "system-rebuild-lock" (
    builtins.readFile ./scripts/system-rebuild-lock
  );
in
pkgs.writeShellScript "guarded-system-rebuild" ''
  export EXCLUSIVE_RUN_LOCK_HELPER=${exclusiveRunLock}/libexec/exclusive-run-lock/exclusive-run-lock.sh
  export EXCLUSIVE_RUN_SCOPE_PYTHON=${pkgs.python312}/bin/python3
  exec ${systemRebuildLockGuard} "$@"
''
