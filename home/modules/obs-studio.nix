{
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  nixglWrap = import ../../lib/nixgl-wrap.nix { inherit pkgs inputs isNixOS; };

  obsStudioPackage = nixglWrap.wrapWithNixGLIntel {
    package = pkgs.obs-studio;
    binaries = [ "obs" ];
  };
in
{
  home.packages = [ obsStudioPackage ];
}
