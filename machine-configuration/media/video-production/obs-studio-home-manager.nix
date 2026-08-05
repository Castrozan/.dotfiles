{
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  nixglWrap = import ../../../lib/nixgl-wrap.nix { inherit pkgs inputs isNixOS; };

  obsStudioNixGLWrappedPackage = nixglWrap.wrapWithNixGLIntel {
    package = pkgs.obs-studio;
    binaries = [ "obs" ];
  };

  ensureObsPersistentRestoreScriptSource = pkgs.writeText "ensure-obs-persistent-restore.py" (
    builtins.readFile ./scripts/ensure_obs_persistent_restore.py
  );

  obsStudioWithPersistentRestoreWrapper = pkgs.symlinkJoin {
    name = "obs-studio-with-persistent-restore";
    paths = [
      (pkgs.writeShellScriptBin "obs" ''
        ${pkgs.python312}/bin/python3 ${ensureObsPersistentRestoreScriptSource} || true
        exec ${obsStudioNixGLWrappedPackage}/bin/obs "$@"
      '')
      obsStudioNixGLWrappedPackage
    ];
  };
in
{
  home.packages = [ obsStudioWithPersistentRestoreWrapper ];
}
