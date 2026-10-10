{
  pkgs,
  lib,
  config,
  hostname,
  ...
}:
let
  systemRebuildLockGuard = import ./system-rebuild-lock-package.nix {
    inherit pkgs;
  };
  guardScript = pkgs.writeShellScript "darwin-rebuild-guard" (
    builtins.readFile ./scripts/darwin-rebuild-guard
  );
  guardedDarwinRebuild = pkgs.writeShellScriptBin "darwin-rebuild" ''
    export REAL_DARWIN_REBUILD=${config.system.build.darwin-rebuild}/bin/darwin-rebuild
    export DARWIN_REBUILD_SHELL=${pkgs.bash}/bin/bash
    export DARWIN_REBUILD_ENTRYPOINT="$0"
    export SYSTEM_REBUILD_LOCK_GUARD=${systemRebuildLockGuard}
    exec ${guardScript} "$@"
  '';
in
{
  security.sudo.extraConfig = ''
    Defaults env_keep += "DOTFILES_EXCLUSIVE_RUN_OWNER"
  '';

  environment.systemPackages = [
    (import ./scripts/rebuild { inherit pkgs hostname; })
    (lib.hiPrio guardedDarwinRebuild)
  ];
}
