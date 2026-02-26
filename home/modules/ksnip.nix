{
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  nixglWrap = import ../../lib/nixgl-wrap.nix { inherit pkgs inputs isNixOS; };

  ksnipPackage = nixglWrap.wrapWithNixGLIntel {
    package = pkgs.ksnip;
    binaries = [ "ksnip" ];
  };
in
{
  home.packages = [ ksnipPackage ];
}
