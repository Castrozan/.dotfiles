{ pkgs }:
let
  exclusiveRunLock = import ../../../agent-harness/session-control/exclusive-run-lock-package.nix {
    inherit pkgs;
  };
  systemRebuildLockGuard = pkgs.writeShellScript "system-rebuild-lock" (
    builtins.readFile ./scripts/system-rebuild-lock
  );
  sentinelGuard = pkgs.writeShellScript "nixos-rebuild-guard" (
    builtins.readFile ./scripts/nixos-rebuild-guard
  );
  stagedScripts = pkgs.runCommand "nixos-staged-rebuild-scripts" { } ''
    mkdir -p $out
    install -m 0644 ${./scripts/nixos-staged-rebuild}/*.py $out/
    install -m 0755 ${./scripts/nixos-staged-rebuild/staged-rebuild} $out/staged-rebuild
    substituteInPlace $out/staged-rebuild \
      --replace-fail '#!/usr/bin/env bash' '#!${pkgs.bash}/bin/bash' \
      --replace-fail '$NIXOS_STAGED_REBUILD_PYTHON' '${pkgs.python3}/bin/python3' \
      --replace-fail '$NIXOS_STAGED_REBUILD_SCRIPTS' "$out"
  '';
  runtimeEnvironment = ''
    export PATH=${
      pkgs.lib.makeBinPath [
        pkgs.nix
        pkgs.git
        pkgs.coreutils
      ]
    }:"$PATH"
    export PYTHONPATH=${pkgs.nixos-rebuild-ng}/${pkgs.python3.sitePackages}
    export PYTHONNOUSERSITE=true
    export REBUILD_COMMAND_TIME=${pkgs.time}/bin/time
  '';
in
{
  prefetch = pkgs.writeShellScript "nixos-rebuild-prefetch" ''
    ${runtimeEnvironment}
    exec ${pkgs.python3}/bin/python3 ${stagedScripts}/prefetch_rebuild.py "$@"
  '';
  rebuild = pkgs.writeShellScript "nixos-staged-rebuild" ''
    ${runtimeEnvironment}
    export REAL_NIXOS_REBUILD=${stagedScripts}/staged-rebuild
    export SYSTEM_REBUILD_LOCK_GUARD=${systemRebuildLockGuard}
    export EXCLUSIVE_RUN_LOCK_HELPER=${exclusiveRunLock}/libexec/exclusive-run-lock/exclusive-run-lock.sh
    export EXCLUSIVE_RUN_SCOPE_PYTHON=${pkgs.python3}/bin/python3
    exec ${sentinelGuard} "$@"
  '';
}
