{ pkgs, hostname }:
let
  exclusiveRunLock =
    import ../../../../../agent-harness/session-control/exclusive-run-lock-package.nix
      {
        inherit pkgs;
      };
  stagedRebuild =
    if pkgs.stdenv.hostPlatform.isLinux then
      import ../../nixos-staged-rebuild-package.nix { inherit pkgs; }
    else
      {
        prefetch = "";
        rebuild = "";
      };
in
pkgs.runCommand "rebuild" { } ''
  mkdir -p $out/bin $out/libexec/rebuild/backends

  install -m 0755 ${./rebuild} $out/bin/rebuild
  install -m 0644 ${./backends/nixos} $out/libexec/rebuild/backends/nixos
  install -m 0644 ${./backends/darwin} $out/libexec/rebuild/backends/darwin
  install -m 0644 ${./backends/home-manager} $out/libexec/rebuild/backends/home-manager

  substituteInPlace $out/bin/rebuild \
    --replace-fail '@machineAlias@' '${hostname}' \
    --replace-fail '@exclusiveRunLockHelper@' '${exclusiveRunLock}/libexec/exclusive-run-lock/exclusive-run-lock.sh' \
    --replace-fail '@exclusiveRunScopePython@' '${pkgs.python3}/bin/python3' \
    --replace-fail '@nixosRebuildPrefetch@' '${stagedRebuild.prefetch}' \
    --replace-fail '@nixosStagedRebuild@' '${stagedRebuild.rebuild}' \
    --replace-fail '@backendsDirectory@' "$out/libexec/rebuild/backends"

  substituteInPlace $out/bin/rebuild \
    --replace-fail '#!/usr/bin/env bash' '#!${pkgs.bash}/bin/bash'
''
